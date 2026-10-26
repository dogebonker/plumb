#!/usr/bin/env node
'use strict';

// Compiler API only: candidate modules and tsconfig plugins are never executed.
const fs = require('node:fs');
const path = require('node:path');
const proof = {complete: false, files: [], exports: [], errors: [], status: 'unsupported'};
let output;
let outputAllowed = false;
const limit = 2000;
function error(message) {
  if (proof.errors.length < 200) proof.errors.push(String(message).slice(0, 2000));
}
function invalid(message) { throw new Error(message); }

function main() {
  const args = process.argv.slice(2);
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    if (!['--root', '--typescript', '--expected', '--output'].includes(args[i]) || !args[i + 1] || options[args[i]])
      invalid('invalid CLI arguments');
    options[args[i]] = args[i + 1];
  }
  output = options['--output'];
  if (Object.keys(options).length !== 4 || Object.values(options).some(p => !path.isAbsolute(p)))
    invalid('root, typescript, expected and output must be absolute paths');
  const outputPath = path.join(fs.realpathSync(path.dirname(output)), path.basename(output));
  const outside = directory => path.relative(directory, outputPath).split(path.sep)[0] === '..';
  if (!outside(path.resolve(options['--root'])))
    invalid('proof output must be outside source root');
  outputAllowed = true;
  const root = fs.realpathSync(options['--root']);
  if (!outside(root)) {
    outputAllowed = false;
    invalid('proof output must be outside source root');
  }
  const ts = require(options['--typescript']);
  for (const name of ['readConfigFile', 'parseJsonConfigFileContent', 'createProgram', 'createCompilerHost', 'createSourceFile'])
    if (typeof ts[name] !== 'function') invalid('unsupported TypeScript compiler API');
  const expected = JSON.parse(fs.readFileSync(options['--expected'], 'utf8'));
  if (!expected || !Array.isArray(expected.files) || !Array.isArray(expected.interfaces) ||
      expected.files.length > limit || expected.interfaces.length > limit) invalid('invalid expected surface');
  function sourcePath(p) {
    if (typeof p !== 'string' || !p || p.includes('\\') || p.split('/').some(x => !x || x === '.' || x === '..') ||
        path.isAbsolute(p) || !/\.(?:ts|tsx|mts|cts)$/.test(p)) invalid('invalid TypeScript source path');
    return path.join(root, p);
  }
  const files = new Set();
  for (const p of expected.files) {
    sourcePath(p);
    if (files.has(p)) invalid('duplicate owned file');
    files.add(p);
  }
  const contracts = new Map();
  for (const item of expected.interfaces) {
    if (!item || !files.has(item.path) || typeof item.symbol !== 'string' || !item.symbol ||
        typeof item.signature !== 'string' || !item.signature.trim() || item.signature.length > 10000)
      invalid('invalid interface declaration');
    const key = item.path + '\0' + item.symbol;
    if (contracts.has(key)) invalid('duplicate interface declaration');
    // Parse the whole alias to prevent a type expression from injecting statements.
    const ast = ts.createSourceFile('contract.ts', 'type __Frozen = ' + item.signature + ';', ts.ScriptTarget.Latest, true);
    if (ast.parseDiagnostics.length || ast.statements.length !== 1 || !ts.isTypeAliasDeclaration(ast.statements[0]))
      invalid('signature must be one TypeScript type expression');
    contracts.set(key, item);
  }
  let failed = false;
  let covered = true;
  const configs = new Map();
  function configFor(filename) {
    const config = ts.findConfigFile(path.dirname(filename), ts.sys.fileExists);
    if (configs.has(config)) return configs.get(config);
    let parsed = {options: {target: ts.ScriptTarget.ESNext, module: ts.ModuleKind.NodeNext,
      moduleResolution: ts.ModuleResolutionKind.NodeNext, jsx: ts.JsxEmit.ReactJSX}, fileNames: []};
    if (config) {
      const read = ts.readConfigFile(config, ts.sys.readFile);
      if (read.error) invalid('cannot read tsconfig: TS' + read.error.code);
      parsed = ts.parseJsonConfigFileContent(read.config, ts.sys, path.dirname(config), undefined, config);
      if (parsed.errors.length) invalid('invalid tsconfig: ' + parsed.errors.map(d => 'TS' + d.code).join(', '));
    }
    parsed.options = {...parsed.options, strict: true, noImplicitAny: true, strictFunctionTypes: true,
      strictNullChecks: true, strictBindCallApply: true, strictPropertyInitialization: true,
      noImplicitThis: true, alwaysStrict: true, useUnknownInCatchVariables: true,
      noEmit: true, incremental: false, composite: false,
      declaration: false, emitDeclarationOnly: false, noCheck: false};
    configs.set(config, parsed);
    return parsed;
  }
  function diagnostic(d, virtual) {
    const location = d.file && d.start !== undefined ? d.file.getLineAndCharacterOfPosition(d.start) : null;
    const name = d.file ? (d.file.fileName === virtual ? 'frozen signature' : path.relative(root, d.file.fileName)) : 'compiler';
    return name + (location ? ':' + (location.line + 1) : '') + ' TS' + d.code + ': ' + ts.flattenDiagnosticMessageText(d.messageText, ' ').slice(0, 1000);
  }
  function authored(declaration) {
    const filename = declaration.getSourceFile().fileName;
    return !filename.split(path.sep).includes('node_modules') && path.relative(root, filename).split(path.sep)[0] !== '..';
  }
  function hasAny(type, checker, node, frozenType) {
    const seen = new Set();
    const frozenDefaults = new Map();
    let visits = 0;
    function visit(current, depth = 0, collect = false, location = '$') {
      if (++visits > 10000 || depth > 96) invalid('type boundary inspection budget exhausted');
      if (current.flags & ts.TypeFlags.Any) return !collect;
      if (seen.has(current)) return false;
      seen.add(current);
      try {
        const symbol = current.aliasSymbol || current.getSymbol();
        const declarations = symbol && symbol.declarations;
        const opaque = declarations && declarations.length && declarations.every(decl => !authored(decl));
        if (current.flags & ts.TypeFlags.TypeParameter && !opaque) {
          for (const bound of [checker.getDefaultFromTypeParameter(current), checker.getBaseConstraintOfType(current)]) {
            if (bound && visit(bound, depth + 1, collect, location + '/bound')) return true;
          }
        }
        let arguments_ = current.aliasTypeArguments || [];
        let parameters = [];
        if (current.aliasSymbol) {
          const declaration = declarations && declarations.find(decl => decl.typeParameters);
          parameters = declaration ? declaration.typeParameters.map(param => checker.getTypeAtLocation(param)) : [];
        } else if (current.flags & ts.TypeFlags.Object && current.objectFlags & ts.ObjectFlags.Reference) {
          arguments_ = checker.getTypeArguments(current);
          parameters = current.target.typeParameters || [];
        }
        for (const [index, argument] of arguments_.entries()) {
          const position = location + '/argument/' + index;
          if (opaque && parameters[index] && checker.getDefaultFromTypeParameter(parameters[index]) === argument) {
            if (collect) {
              frozenDefaults.set(position, {symbol, argument});
              continue;
            }
            // Internal defaults are opaque only when the frozen type requests that exact compiler type.
            const frozen = frozenDefaults.get(position);
            if (frozen?.symbol === symbol && frozen.argument === argument) continue;
          }
          if (visit(argument, depth + 1, collect, position)) return true;
        }
        if (opaque && depth > 0) return false;
        if (current.isUnionOrIntersection() && current.types.some((part, index) =>
            visit(part, depth + 1, collect, location + '/part/' + index))) return true;
        const signatures = [...checker.getSignaturesOfType(current, ts.SignatureKind.Call),
                            ...checker.getSignaturesOfType(current, ts.SignatureKind.Construct)];
        for (const [index, sig] of signatures.entries()) {
          const position = location + '/signature/' + index;
          if ((sig.typeParameters || []).some((parameter, index) =>
              visit(parameter, depth + 1, collect, position + '/type-parameter/' + index))) return true;
          if (visit(checker.getReturnTypeOfSignature(sig), depth + 1, collect, position + '/return')) return true;
          if (sig.getParameters().some((param, index) => visit(checker.getTypeOfSymbolAtLocation(param, node),
              depth + 1, collect, position + '/parameter/' + index))) return true;
        }
        if (opaque || !(current.flags & ts.TypeFlags.Object)) return false;
        for (const property of checker.getPropertiesOfType(current)) {
          if (visit(checker.getTypeOfSymbolAtLocation(property, property.valueDeclaration || node), depth + 1, collect,
                    location + '/property/' + JSON.stringify(property.getName()))) return true;
        }
        return checker.getIndexInfosOfType(current).some((index, position) =>
          visit(index.type, depth + 1, collect, location + '/index/' + position));
      } finally { seen.delete(current); }
    }
    visit(frozenType, 0, true);
    return visit(type);
  }
  for (const relative of files) {
    const filename = sourcePath(relative);
    if (!fs.existsSync(filename)) {
      failed = true; covered = false; error(relative + ': missing file'); continue;
    }
    if (fs.realpathSync(filename) !== filename || !fs.statSync(filename).isFile()) invalid('source symlink or non-file unsupported');
    proof.files.push(relative);
    const parsed = configFor(filename);
    const host = ts.createCompilerHost(parsed.options);
    host.writeFile = () => invalid('compiler attempted source write');
    const program = ts.createProgram([...new Set([...parsed.fileNames, filename])], parsed.options, host);
    const checker = program.getTypeChecker();
    const source = program.getSourceFile(filename);
    if (!source) invalid('compiler did not load owned file');
    if (source.statements.some(node => ts.isExportAssignment(node) && node.isExportEquals))
      invalid('export assignment (export =) surface unsupported');
    const syntax = program.getSyntacticDiagnostics();
    if (syntax.length) covered = false;
    const diagnostics = [...program.getOptionsDiagnostics(), ...program.getGlobalDiagnostics(), ...syntax, ...program.getSemanticDiagnostics()];
    if (diagnostics.length) { failed = true; diagnostics.forEach(d => error(diagnostic(d))); }
    const module = checker.getSymbolAtLocation(source);
    const symbols = module ? checker.getExportsOfModule(module) : [];
    if (symbols.length > limit || proof.exports.length + symbols.length > limit) invalid('export inventory too large');
    const seen = new Set();
    const checks = [];
    for (const exported of symbols) {
      const name = exported.getName();
      seen.add(name);
      const symbol = exported.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(exported) : exported;
      const isValue = !!(symbol.flags & ts.SymbolFlags.Value);
      const type = isValue ? checker.getTypeOfSymbolAtLocation(symbol, source) : checker.getDeclaredTypeOfSymbol(symbol);
      const item = contracts.get(relative + '\0' + name);
      const row = {path: relative, symbol: name, signature: null,
        actual_signature: checker.typeToString(type, source, ts.TypeFormatFlags.NoTruncation).slice(0, 2000), compatible: false};
      proof.exports.push(row);
      if (!item) { failed = true; error(relative + ': unexpected export ' + name); continue; }
      // Inspect only authored boundary annotations; do not recurse through React/library internals.
      let explicitAny = false;
      function inspect(node) {
        if (node.kind === ts.SyntaxKind.AnyKeyword) explicitAny = true;
        ts.forEachChild(node, inspect);
      }
      function inspectBoundary(decl) {
        if (decl.type) inspect(decl.type);
        for (const param of decl.typeParameters || []) inspect(param);
        for (const param of decl.parameters || []) if (param.type) inspect(param.type);
      }
      for (const decl of symbol.declarations || []) {
        if (!authored(decl)) continue;
        inspectBoundary(decl);
        if (ts.isInterfaceDeclaration(decl)) inspect(decl);
        if (decl.initializer && (ts.isArrowFunction(decl.initializer) || ts.isFunctionExpression(decl.initializer)))
          inspectBoundary(decl.initializer);
      }
      if (explicitAny) { failed = true; error(relative + ': explicit any at export boundary ' + name); continue; }
      checks.push({row, item, isValue});
    }
    for (const item of expected.interfaces.filter(i => i.path === relative)) {
      if (!seen.has(item.symbol)) {
        failed = true; error(relative + ': missing export ' + item.symbol);
        proof.exports.push({path: relative, symbol: item.symbol, signature: null, actual_signature: '', compatible: false});
      }
    }
    if (!checks.length) continue;
    // Same directory and extension preserve relative imports and NodeNext module context.
    let virtual = filename.replace(/\.(tsx?|mts|cts)$/, '.__plumb_surface__.$1');
    while (fs.existsSync(virtual)) virtual = virtual.replace('.__plumb_surface__', '.__plumb_surface___');
    const specifier = './' + path.basename(filename).replace(/\.(tsx?|mts|cts)$/, (ext) => ext === '.mts' ? '.mjs' : ext === '.cts' ? '.cjs' : '.js');
    const lines = ['export {};'];
    const ranges = [];
    for (const [index, check] of checks.entries()) {
      const access = ts.isIdentifierText(check.item.symbol, ts.ScriptTarget.Latest) || check.item.symbol === 'default'
        ? '.' + check.item.symbol : '[' + JSON.stringify(check.item.symbol) + ']';
      if (!check.isValue && access.startsWith('[')) invalid('unsupported non-identifier type export');
      const start = lines.join('\n').length + 1;
      lines.push('type __Frozen' + index + ' = ' + check.item.signature + ';',
        'declare const __actual' + index + ': ' + (check.isValue ? 'typeof ' : '') + 'import(' + JSON.stringify(specifier) + ')' + access + ';',
        'const __proof' + index + ': __Frozen' + index + ' = __actual' + index + ';');
      ranges.push({start, end: lines.join('\n').length + 1, index, check});
    }
    const text = lines.join('\n');
    const checkOptions = {...parsed.options, noUnusedLocals: false, noUnusedParameters: false};
    const virtualHost = ts.createCompilerHost(checkOptions);
    const readFile = virtualHost.readFile.bind(virtualHost);
    const fileExists = virtualHost.fileExists.bind(virtualHost);
    virtualHost.readFile = p => p === virtual ? text : readFile(p);
    virtualHost.fileExists = p => p === virtual || fileExists(p);
    virtualHost.writeFile = host.writeFile;
    const checked = ts.createProgram([...new Set([...parsed.fileNames, filename, virtual])], checkOptions, virtualHost);
    const issues = ts.getPreEmitDiagnostics(checked);
    if (issues.length) { failed = true; issues.forEach(d => error(diagnostic(d, virtual))); }
    const verifiedChecker = checked.getTypeChecker();
    const virtualSource = checked.getSourceFile(virtual);
    for (const {start, end, index, check} of ranges) {
      const broken = issues.some(d => !d.file || d.file.fileName !== virtual || d.start === undefined || (d.start >= start && d.start < end));
      if (broken) continue;
      const frozen = virtualSource.statements[1 + index * 3];
      const actual = virtualSource.statements[2 + index * 3].declarationList.declarations[0];
      if (hasAny(verifiedChecker.getTypeAtLocation(actual.name), verifiedChecker, actual,
                 verifiedChecker.getTypeFromTypeNode(frozen.type))) {
        failed = true; error(relative + ': any at export boundary ' + check.item.symbol); continue;
      }
      check.row.compatible = true; check.row.signature = check.item.signature;
    }
  }
  proof.complete = covered;
  proof.status = failed || !covered ? 'fail' : 'pass';
  return proof.status === 'pass' ? 0 : 1;
}

let code = 2;
try { code = main(); } catch (e) { proof.complete = false; proof.status = 'unsupported'; error(e.message); }
if (!output) {
  const index = process.argv.indexOf('--output');
  if (index !== -1) output = process.argv[index + 1];
}
try {
  if (outputAllowed) fs.writeFileSync(output, JSON.stringify(proof) + '\n', {flag: 'wx'});
  else process.stderr.write('surface checker requires --output absolute path\n');
} catch (e) { process.stderr.write('cannot write surface proof\n'); code = 2; }
process.exitCode = code;
