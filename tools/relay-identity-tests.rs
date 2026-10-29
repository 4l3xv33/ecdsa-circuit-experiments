use quantum_ecc::circuit::{Op, OperationType as K, QubitId, BitId};
use quantum_ecc::sim::Simulator;
use sha3::digest::XofReader;

struct Words { values: [u64;2], consumed: usize }
impl XofReader for Words {
    fn read(&mut self, bytes: &mut [u8]) {
        assert_eq!(bytes.len(),8);
        bytes.copy_from_slice(&self.values[self.consumed].to_le_bytes());
        self.consumed+=1;
    }
}
fn op(k:K,a:Option<u64>,b:Option<u64>,t:u64,bit:Option<u64>,cond:Option<u64>)->Op {
    let mut o=Op::empty();o.kind=k;o.q_target=QubitId(t);
    if let Some(a)=a {o.q_control2=QubitId(a);}
    if let Some(b)=b {o.q_control1=QubitId(b);}
    if let Some(b)=bit {o.c_target=BitId(b);}
    if let Some(b)=cond {o.c_condition=BitId(b);}
    o.validate();o
}
fn x(t:u64)->Op {op(K::X,None,None,t,None,None)}
fn cx(a:u64,t:u64)->Op {op(K::CX,None,Some(a),t,None,None)}
fn sw(a:u64,t:u64)->Op {op(K::Swap,None,Some(a),t,None,None)}
fn cc(a:u64,b:u64,t:u64)->Op {op(K::CCX,Some(a),Some(b),t,None,None)}
fn hm(t:u64,b:u64)->Op {op(K::Hmr,None,None,t,Some(b),None)}
fn cz(a:u64,b:u64,c:u64)->Op {op(K::CZ,None,Some(a),b,None,Some(c))}

fn circuits(c1:bool,c2:bool)->(Vec<Op>,Vec<Op>) {
    let base=vec![cc(0,1,2),cx(2,7),hm(2,0),cz(0,1,0),cx(5,9),
                  cc(0,1,6),cx(6,8),hm(6,1),cz(0,1,1),cx(5,9)];
    let mut candidate=vec![cc(0,1,2),cx(2,7)];
    if c1 {candidate.push(x(3));}
    candidate.extend([sw(2,3),hm(2,0),cx(5,4)]);
    if c2 {candidate.push(x(4));}
    candidate.push(sw(3,4));
    if c1 {candidate.push(x(3));}
    candidate.extend([cx(5,9),sw(4,6),cx(5,4)]);
    if c2 {candidate.push(x(4));}
    candidate.extend([cx(6,8),hm(6,1),cz(0,1,1),cx(5,9)]);
    (base,candidate)
}

#[test]
fn exhaustive_relay_value_phase_and_random_word_identity() {
    let mut cases=0;
    for c1 in [false,true] {for c2 in [false,true] {
        let (base,candidate)=circuits(c1,c2);
        for m0 in [0,u64::MAX] {for m1 in [0,u64::MAX] {
            let mut r0=Words{values:[m0,m1],consumed:0};
            let mut r1=Words{values:[m0,m1],consumed:0};
            let mut a=Simulator::new(10,2,&mut r0);
            let mut b=Simulator::new(10,2,&mut r1);
            for (bit,q) in [0,1,5,7,8,9].into_iter().enumerate() {
                let value=(0..64).fold(0u64,|v,lane|v|(((lane>>bit)&1) as u64)<<lane);
                a.qubits[q]=value;b.qubits[q]=value;
            }
            a.qubits[3]=if c1 {u64::MAX}else{0};b.qubits[3]=a.qubits[3];
            a.qubits[4]=a.qubits[5]^if c2 {u64::MAX}else{0};b.qubits[4]=a.qubits[4];
            a.apply_iter(base.iter());b.apply_iter(candidate.iter());
            assert_eq!(a.qubits,b.qubits,"borrowed wires and output values");
            assert_eq!(a.bits,b.bits,"measurement outcomes");
            assert_eq!(a.phase,0);assert_eq!(b.phase,0);
            assert_eq!(a.stats.toffoli_gates-b.stats.toffoli_gates,64);
            drop(a);drop(b);
            assert_eq!(r0.consumed,2);assert_eq!(r1.consumed,2);
            cases+=64;
        }}
    }}
    assert_eq!(cases,1024);
    println!("1024 exhaustive input/measurement/constant combinations passed");
}

#[test]
fn negative_control_detects_missing_twin_restoration() {
    let (base,mut candidate)=circuits(false,false);
    let restore=candidate.iter().rposition(|o|o.kind==K::CX&&o.q_control1.0==5&&o.q_target.0==4).unwrap();
    candidate.remove(restore);
    let mut r0=Words{values:[u64::MAX,u64::MAX],consumed:0};
    let mut r1=Words{values:[u64::MAX,u64::MAX],consumed:0};
    let mut a=Simulator::new(10,2,&mut r0);let mut b=Simulator::new(10,2,&mut r1);
    for s in [&mut a,&mut b] {s.qubits[0]=u64::MAX;s.qubits[1]=u64::MAX;s.qubits[4]=u64::MAX;s.qubits[5]=u64::MAX;}
    a.apply_iter(base.iter());b.apply_iter(candidate.iter());
    assert_ne!(a.qubits,b.qubits,"fixture must catch an un-restored donor");
}
