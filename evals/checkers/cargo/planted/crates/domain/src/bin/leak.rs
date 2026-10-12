// Planted violation: the domain crate uses a driven adapter crate. A file under src/bin/ is built
// without editing lib.rs, so one new file is enough.
use shop_clock::now;

fn main() {
    let _ = now();
}
