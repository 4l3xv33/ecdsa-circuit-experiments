pub use quantum_ecc::circuit;
use circuit::{Op,OperationType as K,QubitId,BitId,RegisterId};
use std::io::Read;
#[allow(dead_code)] #[path="ring-cond.rs"] mod cond_pass;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/sqtop_pass.rs"] mod sqtop_pass;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/affine_simplify.rs"] mod affine_simplify;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/quadratic_simplify.rs"] mod quadratic_simplify;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/classical_factors_xor.rs"] mod classical_factors_xor;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/classical_wide/mod.rs"] mod classical_wide;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/pscan.rs"] mod pscan;
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/zero_force.rs"] mod zero_force;
fn main(){
 let p=std::env::args().nth(1).unwrap();let mut f=std::fs::File::open(p).unwrap();
 let mut h=[0u8;16];f.read_exact(&mut h).unwrap();assert_eq!(&h[..8],b"QECCOPSZ");
 let n=u64::from_le_bytes(h[8..].try_into().unwrap()) as usize;assert!(n<20000000);
 let mut d=zstd::stream::read::Decoder::new(std::io::BufReader::new(f)).unwrap();
 let kinds=[K::Neg,K::Register,K::AppendToRegister,K::BitInvert,K::BitStore0,K::BitStore1,K::X,K::Z,K::CX,K::CZ,K::Swap,K::R,K::Hmr,K::CCX,K::CCZ,K::PushCondition,K::PopCondition,K::DebugPrint];
 let mut ops=Vec::with_capacity(n);let mut r=[0u8;56];
 for _ in 0..n {d.read_exact(&mut r).unwrap();let a:Vec<u64>=r.chunks_exact(8).map(|x|u64::from_le_bytes(x.try_into().unwrap())).collect();
 let o=Op{kind:kinds[a[0] as usize],q_control2:QubitId(a[1]),q_control1:QubitId(a[2]),q_target:QubitId(a[3]),c_target:BitId(a[4]),c_condition:BitId(a[5]),r_target:RegisterId(a[6])};o.validate();ops.push(o);}
 eprintln!("loaded {} ops",ops.len());
 std::env::set_var("SL_COND", "mufsr");
 let before=ops.len();
 let mut v=classical_factors_xor::simplify_classical(ops);
 v=classical_wide::simplify_classical(v);
 v=cond_pass::run(v);
 std::env::set_var("SL_SQTOP", "1");v=sqtop_pass::run(v);
 // Do not fix measurement outcomes: preserve both branches.
 v=classical_factors_xor::simplify_classical(v);
 v=classical_wide::simplify_classical(v);
 println!("before_ops={before} after_ops={}",v.len());
 if let Some(out)=std::env::args().nth(2){
  use std::io::Write;
  let mut f=std::fs::File::create(out).unwrap();
  f.write_all(b"QECCOPSZ").unwrap();f.write_all(&(v.len() as u64).to_le_bytes()).unwrap();
  let mut z=zstd::stream::write::Encoder::new(f,3).unwrap();
  for o in &v{for a in [o.kind as u64,o.q_control2.0,o.q_control1.0,o.q_target.0,o.c_target.0,o.c_condition.0,o.r_target.0]{z.write_all(&a.to_le_bytes()).unwrap();}}
  z.finish().unwrap();
 }
}
