use shop_domain::{total, Order};

#[derive(Default)]
pub struct Repo {
    rows: Vec<Order>,
}

impl Repo {
    pub fn add(&mut self, order: Order) -> u64 {
        self.rows.push(order);
        total(&self.rows)
    }
}
