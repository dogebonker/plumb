package domain

// Planted violation: identity's domain imports billing's adapters, past billing's nested internal/.
import "example.com/shop/internal/billing/internal/adapters"

var Ledger adapters.Store
