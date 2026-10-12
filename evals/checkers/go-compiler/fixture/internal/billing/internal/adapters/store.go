package adapters

import "example.com/shop/internal/billing/internal/domain"

type Store struct{ rows []domain.Invoice }

func (s *Store) Add(inv domain.Invoice) int {
	s.rows = append(s.rows, inv)
	return len(s.rows)
}
