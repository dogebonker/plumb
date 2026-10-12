pub struct Order {
    pub id: String,
    pub cents: u64,
}

pub fn total(orders: &[Order]) -> u64 {
    orders.iter().map(|o| o.cents).sum()
}
