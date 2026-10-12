package domain

type Order struct {
	ID    string
	Cents int
}

func Total(orders []Order) int {
	sum := 0
	for _, o := range orders {
		sum += o.Cents
	}
	return sum
}
