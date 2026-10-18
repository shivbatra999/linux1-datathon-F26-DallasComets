import {config} from './config.js';
import {menu as seedMenu, orders as seedOrders} from './fixtures.js';
export const isDemo=config.mode==='demo';
let orders=structuredClone(seedOrders);
let profile={name:'Jamie Davis',phone:'',address:''};
const copy=v=>structuredClone(v);
async function request(path,options={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),config.timeoutMs);
 try{
 const res=await fetch(config.apiBase+path,{...options,headers:{'Content-Type':'application/json',...options.headers},credentials:'same-origin',signal:controller.signal});
 const data=res.status===204?null:await res.json();
 if(!res.ok)throw new Error(typeof data?.detail==='string'?data.detail:`Request failed (${res.status}).`);
 return data;
 }catch(e){if(e.name==='AbortError')throw new Error('Request timed out. Please retry.');throw e}finally{clearTimeout(timer)}
}
const json=(method,body)=>({method,body:JSON.stringify(body)});
let activeBusinessId=null;
const api={
 login:body=>request('/auth/login',json('POST',{
  email:body.username.trim(),
  password:body.password
 })),
 logout:()=>request('/auth/logout',{method:'POST'}),
 me:()=>request('/auth/me'),
 bootstrap:async role=>{
  if(role==='customer'){
   const businesses=await request('/businesses');
   const business=businesses[0];
   if(!business)throw new Error('No active catering business is available.');
   activeBusinessId=business.id;
   const [menu,orders]=await Promise.all([
    request('/businesses/'+encodeURIComponent(business.id)+'/menu'),
    request('/orders/mine')
   ]);
   return {menu,orders,business};
  }
  if(role==='owner'){const [menu,orders]=await Promise.all([request('/owner/menu'),request('/owner/orders')]);return {menu,orders,businesses:[]}}
  throw new Error('Unsupported account role.');
 },
 recommend:body=>request('/ai/recommendations',json('POST',{...body,business_id:activeBusinessId})),
 placeOrder:body=>request('/orders',json('POST',{...body,business_id:activeBusinessId})),
 summary:()=>request('/ai/summary',{method:'POST'}),
 profile:()=>request('/profile'),
 saveProfile:body=>request('/profile',json('PUT',body))
};
function demoUser(){const user=JSON.parse(sessionStorage.getItem('simplecater-demo-user')||'null');if(!user)throw new Error('Sign in first.');return user}
function requireDemoRole(expected){if(demoUser().role!==expected)throw new Error('Access denied.');}
const demo={
 login:async({username,password})=>{if(!['customer','owner'].includes(username)||password!=='demo')throw new Error('Use a listed sample account.');const user={id:username==='customer'?1:2,role:username};sessionStorage.setItem('simplecater-demo-user',JSON.stringify(user));return user},
 logout:async()=>sessionStorage.removeItem('simplecater-demo-user'),
 me:async()=>demoUser(),
 bootstrap:async role=>{requireDemoRole(role);return copy({menu:seedMenu,orders:role==='customer'?orders.filter(o=>o.mine):orders})},
 recommend:async ({selected_item_id,cart_item_ids})=>{requireDemoRole('customer');const pairs={1:[5,6],2:[5,6],3:[5,4],4:[5,6],5:[2,6],6:[5,4]};return (pairs[selected_item_id]||[]).filter(id=>!cart_item_ids.includes(id)).map(item_id=>({item_id,reason:'Illustrative pairing for this selection. Connect the model for measured order-pattern evidence.',source:'demo'}))},
 placeOrder:async body=>{requireDemoRole('customer');const items=body.items.map(i=>{const m=seedMenu.find(m=>m.id===i.menu_item_id);if(!m||!Number.isInteger(i.quantity)||i.quantity<1)throw new Error('Invalid order item.');return {...m,quantity:i.quantity}});const order={id:'SC-'+(1049+orders.length-seedOrders.length),items:items.map(m=>`${m.name} × ${m.quantity}`).join(', '),total:items.reduce((s,m)=>s+m.price*m.quantity,0),date:body.pickup_date,status:'Confirmed',mine:true};orders.unshift(order);return copy(order)},
 summary:async()=>{requireDemoRole('owner');return {text:`Your ${orders.length} sample orders total $${orders.reduce((s,o)=>s+o.total,0).toFixed(2)}. Iced tea is an illustrative next-item suggestion. This preview does not run AI models.`,source:'demo',prediction_reason:'Preview only: replace with the predictive model’s item ranking and verified supporting counts.'}},
 profile:async()=>{requireDemoRole('customer');return copy(profile)},saveProfile:async body=>{requireDemoRole('customer');profile={...body};return copy(profile)}
};
export const service=isDemo?demo:api;
