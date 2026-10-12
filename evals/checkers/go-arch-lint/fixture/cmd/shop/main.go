package main

import (
	"fmt"

	"example.com/shop/internal/adapters/memory"
	"example.com/shop/internal/domain"
)

func main() {
	var repo memory.Repo
	fmt.Println(repo.Add(domain.Order{ID: "1", Cents: 100}))
}
