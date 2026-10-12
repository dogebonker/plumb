// Package billing is the module's public facade; the nested internal/ keeps the rest private.
package billing

import (
	"example.com/shop/internal/billing/internal/adapters"
	"example.com/shop/internal/billing/internal/domain"
)

var store adapters.Store

func Charge(id string, cents int) int {
	return store.Add(domain.Invoice{ID: id, Cents: cents})
}
