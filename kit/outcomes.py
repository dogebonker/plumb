"""Report explicit post-merge observations, never infer missing telemetry as zero."""
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


def record(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError('invalid record fields; expected ' + ', '.join(required))
    return value


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('expected nonempty text')
    return value


def timestamp(value, as_of):
    try:
        parsed = datetime.fromisoformat(text(value).replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('expected timezone-aware ISO timestamp') from exc
    if parsed.tzinfo is None or parsed > as_of:
        raise ValueError('timestamp must have timezone and must not be in the future')
    return parsed


def proof(value, confidence):
    text(value['evidence'])
    if value['confidence'] not in confidence:
        raise ValueError('invalid confidence')


def report(data):
    record(data, ('as_of', 'window_days', 'features', 'incidents'))
    as_of = timestamp(data['as_of'], datetime.now(timezone.utc))
    days = data['window_days']
    if type(days) is not int or not 1 <= days <= 3650:
        raise ValueError('window_days must be an integer between 1 and 3650')
    if not isinstance(data['features'], list) or not isinstance(data['incidents'], list):
        raise TypeError('features and incidents must be lists')
    features = {}
    for feature in data['features']:
        record(feature, ('id', 'arm', 'merge_sha', 'merged_at'), ('observation', 'adoption'))
        identity = text(feature['id'])
        text(feature['arm'])
        if identity in features:
            raise ValueError('duplicate feature id: ' + identity)
        merged = feature['merged_at']
        sha = feature['merge_sha']
        if (sha is None) != (merged is None):
            raise ValueError('merge_sha and merged_at must both be present or both null')
        if merged is not None and (not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', sha)):
            raise ValueError('expected full merge SHA')
        merged = timestamp(merged, as_of) if merged is not None else None
        observation = feature.get('observation')
        adoption = feature.get('adoption')
        if merged is None and (observation is not None or adoption is not None):
            raise ValueError('unmerged feature cannot have post-merge observations')
        through = None
        if observation is not None:
            record(observation, ('through', 'confidence', 'evidence'))
            proof(observation, ('confirmed', 'reported'))
            through = timestamp(observation['through'], as_of)
            if through < merged:
                raise ValueError('observation precedes merge')
        if adoption is not None:
            record(adoption, ('event', 'population', 'eligible', 'adopted', 'through', 'confidence', 'evidence'))
            proof(adoption, ('confirmed', 'reported'))
            text(adoption['event'])
            text(adoption['population'])
            if timestamp(adoption['through'], as_of) < merged:
                raise ValueError('adoption observation precedes merge')
            eligible, adopted = adoption['eligible'], adoption['adopted']
            if type(eligible) is not int or type(adopted) is not int or not 0 <= adopted <= eligible:
                raise ValueError('adoption counts must be integers: 0 <= adopted <= eligible')
            adoption = dict(adoption, rate=adopted / eligible if eligible else None)
        end = merged + timedelta(days=days) if merged else None
        complete = bool(end and end <= as_of and through and through >= end
                        and observation['confidence'] == 'confirmed')
        features[identity] = {'id': identity, 'arm': feature['arm'], 'merge_sha': sha,
                              'merged_at': feature['merged_at'],
                              'window_end': end.isoformat() if end else None,
                              'status': 'observed' if complete else 'pending' if not merged else 'incomplete',
                              'observation': observation, 'escaped_defects': 0 if complete else None,
                              'confirmed_defects_lower_bound': 0 if observation else None,
                              'suspected_defects': 0 if observation else None, 'adoption': adoption}
    seen, recovery = {}, []
    for incident in data['incidents']:
        record(incident, ('id', 'feature', 'merge_sha', 'detected_at', 'recovered_at', 'confidence', 'evidence'))
        identity = text(incident['id'])
        proof(incident, ('confirmed', 'suspected'))
        feature = features.get(incident['feature'])
        if not feature or feature['merged_at'] is None or feature['merge_sha'] != incident['merge_sha']:
            raise ValueError('incident must match an existing merged feature and its SHA')
        detected = timestamp(incident['detected_at'], as_of)
        merged = timestamp(feature['merged_at'], as_of)
        recovered = timestamp(incident['recovered_at'], as_of) if incident['recovered_at'] is not None else None
        if detected < merged or (recovered is not None and recovered < detected):
            raise ValueError('invalid detection/recovery ordering')
        if identity in seen:
            if seen[identity] != incident:
                raise ValueError('conflicting incident id: ' + identity)
            continue
        seen[identity] = incident
        if detected >= merged + timedelta(days=days):
            continue
        key = 'confirmed_defects_lower_bound' if incident['confidence'] == 'confirmed' else 'suspected_defects'
        feature[key] = (feature[key] or 0) + 1
        if incident['confidence'] == 'confirmed':
            if feature['escaped_defects'] is not None:
                feature['escaped_defects'] += 1
            recovery.append(dict(incident, right_censored=recovered is None,
                                 recovered_seconds=(recovered - detected).total_seconds() if recovered else None,
                                 ongoing_seconds=(as_of - detected).total_seconds() if recovered is None else None))
    cohorts = []
    for arm in sorted({feature['arm'] for feature in features.values()}):
        members = [feature for feature in features.values() if feature['arm'] == arm]
        observed = [feature for feature in members if feature['status'] == 'observed']
        defects = sum(feature['escaped_defects'] for feature in observed) if observed else None
        cohorts.append({'arm': arm, 'features': len(members),
                        'merged_features': sum(feature['merged_at'] is not None for feature in members),
                        'observed_features': len(observed), 'confirmed_defects': defects,
                        'defects_per_feature': defects / len(observed) if observed else None})
    return {'as_of': data['as_of'], 'window_days': days, 'features': list(features.values()),
            'cohorts': cohorts, 'recovery': recovery}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('report',))
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = report(json.loads(args.input.read_text()))
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
