package domain

// Planted violation: domain imports a driven adapter.
import "example.com/shop/internal/adapters/clock"

var CreatedAt = clock.Now()
