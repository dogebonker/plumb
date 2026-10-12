package main

import (
	"fmt"

	"example.com/shop/internal/billing"
	"example.com/shop/internal/identity"
)

func main() {
	fmt.Println(identity.Guest().ID, billing.Charge("1", 100))
}
