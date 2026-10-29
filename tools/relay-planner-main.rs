pub use quantum_ecc::circuit;
use circuit::{Op,OperationType as K,QubitId,BitId,RegisterId};
use std::io::Read;
#[allow(dead_code)] #[path="relay-planner.rs"] mod pscan_census;
fn main(){
 let p=std::env::args().nth(1).unwrap();let mut f=std::fs::File::open(p).unwrap();
 let mut h=[0u8;16];f.read_exact(&mut h).unwrap();assert_eq!(&h[..8],b"QECCOPSZ");
 let n=u64::from_le_bytes(h[8..].try_into().unwrap()) as usize;assert!(n<20000000);
 let mut d=zstd::stream::read::Decoder::new(std::io::BufReader::new(f)).unwrap();
 let kinds=[K::Neg,K::Register,K::AppendToRegister,K::BitInvert,K::BitStore0,K::BitStore1,K::X,K::Z,K::CX,K::CZ,K::Swap,K::R,K::Hmr,K::CCX,K::CCZ,K::PushCondition,K::PopCondition,K::DebugPrint];
 let mut ops=Vec::with_capacity(n);let mut r=[0u8;56];
 for _ in 0..n {d.read_exact(&mut r).unwrap();let a:Vec<u64>=r.chunks_exact(8).map(|x|u64::from_le_bytes(x.try_into().unwrap())).collect();
 let o=Op{kind:kinds[a[0] as usize],q_control2:QubitId(a[1]),q_control1:QubitId(a[2]),q_target:QubitId(a[3]),c_target:BitId(a[4]),c_condition:BitId(a[5]),r_target:RegisterId(a[6])};o.validate();ops.push(o);}
 eprintln!("loaded {} ops",ops.len());pscan_census::lifetime_census(&ops);
}
