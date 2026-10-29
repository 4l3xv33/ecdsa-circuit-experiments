pub use quantum_ecc::circuit;
use circuit::{Op,OperationType as K,NO_BIT,NO_QUBIT};
#[allow(dead_code)] #[path="../ecdsafail-attempt/src/point_add/cond_pass.rs"] mod cond_pass;
fn gate(k:K,a:Option<u64>,b:Option<u64>,t:Option<u64>,ct:Option<u64>,cc:Option<u64>)->Op{
 let mut o=Op::empty();o.kind=k;
 o.q_control1.0=a.unwrap_or(u64::MAX);o.q_control2.0=b.unwrap_or(u64::MAX);
 o.q_target.0=t.unwrap_or(u64::MAX);o.c_target.0=ct.unwrap_or(u64::MAX);o.c_condition.0=cc.unwrap_or(u64::MAX);o.validate();o
}
fn run(ops:&[Op],mut q:Vec<bool>,mut b:Vec<bool>,measurement:bool)->(Vec<bool>,Vec<bool>,bool){
 b.resize(64,false);let mut base=true;let mut stack=Vec::new();let mut phase=false;
 for o in ops {let cond=base&&(o.c_condition==NO_BIT||b[o.c_condition.0 as usize]);
  let t=o.q_target.0 as usize;let a=o.q_control1.0 as usize;let d=o.q_control2.0 as usize;let cb=o.c_target.0 as usize;
  match o.kind {
   K::PushCondition=>{stack.push(base);base=cond;},K::PopCondition=>base=stack.pop().unwrap(),
   K::X if cond=>q[t]^=true,K::CX if cond=>q[t]^=q[a],K::CCX if cond=>q[t]^=q[a]&q[d],
   K::Swap if cond=>q.swap(t,a),K::Z if cond=>phase^=q[t],K::CZ if cond=>phase^=q[t]&q[a],K::CCZ if cond=>phase^=q[t]&q[a]&q[d],K::Neg if cond=>phase^=true,
   K::Hmr|K::R if cond=>{phase^=q[t]&measurement;q[t]=false;if o.kind==K::Hmr{b[cb]=measurement;}},
   K::BitStore0 if cond=>b[cb]=false,K::BitStore1 if cond=>b[cb]=true,K::BitInvert if cond=>b[cb]^=true,
   _=>{}
  }
 }
 assert!(stack.is_empty());(q,b,phase)
}
fn main(){
 std::env::set_var("SL_COND","r");let mut cases=0;
 for measured_end in [false,true] {for swapped in [false,true] {
  let mut v=vec![gate(K::CCX,Some(0),Some(1),Some(4),None,None),gate(K::PushCondition,None,None,None,None,Some(0)),gate(K::CX,Some(2),None,Some(4),None,Some(1)),gate(K::CCX,Some(1),Some(3),Some(4),None,None),gate(K::PopCondition,None,None,None,None,None)];
  let t=if swapped{v.push(gate(K::Swap,Some(4),None,Some(5),None,None));5}else{4};
  v.push(gate(K::X,None,None,Some(t),None,Some(2)));
  v.push(gate(K::CCX,Some(0),Some(2),Some(t),None,Some(1)));
  v.push(gate(if measured_end{K::Hmr}else{K::R},None,None,Some(t),measured_end.then_some(3),None));
  let new=cond_pass::run(v.clone());assert!(new.iter().filter(|o|o.kind==K::CCX).count()<v.iter().filter(|o|o.kind==K::CCX).count());
  for x in 0..64 {for b in 0..8 {for outcome in [false,true]{
   let q=(0..6).map(|i|x>>i&1!=0).collect::<Vec<_>>();let bits=(0..4).map(|i|b>>i&1!=0).collect::<Vec<_>>();
   let old=run(&v,q.clone(),bits.clone(),outcome);let new=run(&new,q,bits,outcome);
   assert_eq!(old.0,new.0);let used=if measured_end{4}else{3};assert_eq!(old.1[..used],new.1[..used]);assert_eq!(old.2,new.2);cases+=1;
  }}}
 }}
 println!("{{\"cases\":{cases},\"all_input_target_values_included\":true,\"both_measurement_outcomes\":true,\"swap_and_conditional_writes\":true,\"values_and_phase_match\":true}}");
 let _=NO_QUBIT;
}
