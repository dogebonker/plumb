package memory

import "example.com/shop/internal/domain"

type Repo struct{ rows []domain.Order }

func (r *Repo) Add(o domain.Order) int {
	r.rows = append(r.rows, o)
	return domain.Total(r.rows)
}
