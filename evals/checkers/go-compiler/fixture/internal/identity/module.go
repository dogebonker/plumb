// Package identity is the module's public facade.
package identity

import "example.com/shop/internal/identity/internal/domain"

func Guest() domain.User { return domain.User{ID: "guest"} }
