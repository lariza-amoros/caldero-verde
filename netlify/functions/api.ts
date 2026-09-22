declare const Netlify: { env: { get(name: string): string | undefined } };

import { fuzzy } from "fast-fuzzy";
import { timingSafeEqual } from "node:crypto";

type Row = Record<string, any>;

const PRODUCTS = [
  ["Arroz","Granos","lb",185],["Habichuelas","Legumbres","lb"],["Gandules","Legumbres","lata"],
  ["Garbanzos","Legumbres","lata"],["Lentejas","Legumbres","lb"],["Pasta","Granos","lb"],
  ["Avena","Granos","cup"],["Harina de maíz","Granos","lb"],["Pan","Granos","rebanada"],
  ["Galletas de soda","Granos","paquete"],["Pollo","Proteínas","lb"],["Carne de res","Proteínas","lb"],
  ["Cerdo","Proteínas","lb"],["Pescado","Proteínas","lb"],["Atún enlatado","Proteínas","lata"],
  ["Huevos","Proteínas","unit"],["Tomates","Vegetales","unit"],["Cebolla","Vegetales","unit"],
  ["Ajo","Vegetales","diente"],["Pimiento","Vegetales","unit"],["Ají dulce","Vegetales","unit"],
  ["Calabaza","Vegetales","lb"],["Guineos","Frutas","unit"],["Plátanos","Frutas","unit"],
  ["Yuca","Viandas","lb"],["Yautía","Viandas","lb"],["Batata","Viandas","lb"],
  ["Aceite","Aceites y grasas","ml"],["Leche","Lácteos","cup"],["Sal","Condimentos","tsp"],
  ["Azúcar","Condimentos","cup"]
].map(([name,category,default_unit,grams_per_cup])=>({name,category,default_unit,...(grams_per_cup?{grams_per_cup}:{})}));

const UNIT_ALIASES: Record<string,string> = {
  g:"g",gramo:"g",gramos:"g",kg:"kg",kilogramo:"kg",kilogramos:"kg",oz:"oz",onza:"oz",onzas:"oz",
  lb:"lb",libra:"lb",libras:"lb",ml:"ml",mililitro:"ml",mililitros:"ml",l:"l",litro:"l",litros:"l",
  taza:"cup",tazas:"cup",cup:"cup",cups:"cup",cucharada:"tbsp",cucharadas:"tbsp",tbsp:"tbsp",
  cucharadita:"tsp",cucharaditas:"tsp",tsp:"tsp",unidad:"unit",unidades:"unit",unit:"unit"
};
const MASS: Record<string,number>={g:1,kg:1000,oz:28.349523125,lb:453.59237};
const VOLUME: Record<string,number>={ml:1,l:1000,tsp:4.92892159375,tbsp:14.78676478125,cup:236.5882365};
const jsonHeaders={"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"};
const writeWindows=new Map<string,{count:number;reset:number}>();

class HttpError extends Error {
  status:number;
  constructor(status:number,message:string){super(message);this.status=status}
}

export function normalize(value: unknown){return String(value??"").trim().toLocaleLowerCase("es").normalize("NFD").replace(/[\u0300-\u036f]/g,"")}
export function namesMatch(left:unknown,right:unknown){
  const a=normalize(left),b=normalize(right);
  return a===b||(Math.min(a.length,b.length)>=4&&fuzzy(a,b)>=0.92);
}
function canonical(value: unknown){const unit=normalize(value);return UNIT_ALIASES[unit]||unit}
function profile(name: unknown){const target=normalize(name);return PRODUCTS.find(item=>normalize(item.name)===target)}
export function convert(value:number,from:unknown,to:unknown,ingredient:unknown):number|null{
  const source=canonical(from),target=canonical(to);
  if(source===target)return value;
  if(source in MASS&&target in MASS)return value*MASS[source]/MASS[target];
  if(source in VOLUME&&target in VOLUME)return value*VOLUME[source]/VOLUME[target];
  const grams=profile(ingredient)?.grams_per_cup;
  if(grams&&source in MASS&&target in VOLUME)return value*MASS[source]/grams*VOLUME.cup/VOLUME[target];
  if(grams&&source in VOLUME&&target in MASS)return value*VOLUME[source]/VOLUME.cup*grams/MASS[target];
  return null;
}

function response(body:unknown,status=200){return new Response(JSON.stringify(body),{status,headers:jsonHeaders})}
function env(name:string){return Netlify.env.get(name)||""}
function dbHeaders(extra:Record<string,string>={}){
  const key=env("SUPABASE_SECRET_KEY");
  return {apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json",...extra};
}
async function db(path:string,init:RequestInit={}){
  const base=env("SUPABASE_URL").replace(/\/$/,"");
  if(!base||!env("SUPABASE_SECRET_KEY"))throw new Error("Configuración de Supabase incompleta.");
  const res=await fetch(`${base}/rest/v1/${path}`,{...init,headers:{...dbHeaders(),...(init.headers||{})}});
  const text=await res.text();
  const body=text?JSON.parse(text):null;
  if(!res.ok)throw new Error(body?.message||body?.hint||`Supabase ${res.status}`);
  return {body,headers:res.headers};
}

function buildLots(products:Row[],leftovers:Row[]){
  const today=new Date();today.setHours(0,0,0,0);
  return [["product",products],["leftover",leftovers]].flatMap(([source,rows]:any)=>rows.filter((row:Row)=>Number(row.quantity)>0).map((row:Row)=>{
    const expiry=new Date(`${row.expiration_date}T00:00:00`);
    return {...row,source,expired:expiry<today,days_until_expiration:Math.round((expiry.getTime()-today.getTime())/86400000)};
  })).sort((a,b)=>Number(a.expired)-Number(b.expired)||String(a.expiration_date).localeCompare(String(b.expiration_date))||String(a.name).localeCompare(String(b.name)));
}

export function availability(ingredients:Row[],lots:Row[]){
  const details=ingredients.map(ingredient=>{
    let available=0;let convertible=false;const availableUnits=new Set<string>();
    for(const lot of lots){
      if(lot.expired||Number(lot.quantity)<=0||!namesMatch(lot.name,ingredient.ingredients_name))continue;
      availableUnits.add(String(lot.unit));
      const amount=convert(Number(lot.quantity),lot.unit,ingredient.unit,ingredient.ingredients_name);
      if(amount!==null){available+=amount;convertible=true}
    }
    const required=Number(ingredient.quantity),enough=available+1e-9>=required;
    return {ingredient:ingredient.ingredients_name,unit:ingredient.unit,required,available,enough,...(!enough?{missing:Math.max(0,required-available),reason:!convertible&&availableUnits.size?"incompatible_unit":"insufficient_quantity",...(!convertible&&availableUnits.size?{available_units:[...availableUnits]}:{})}:{})};
  });
  const missing=details.filter(item=>!item.enough);
  return {can_prepare:missing.length===0,status:missing.length?"Te faltan ingredientes":"Puedes preparar",details,missing};
}

function consumptionPlan(ingredients:Row[],lots:Row[]){
  const updates:Row[]=[];
  for(const ingredient of ingredients){
    let needed=Number(ingredient.quantity);
    const candidates=lots.filter(lot=>!lot.expired&&Number(lot.quantity)>0&&namesMatch(lot.name,ingredient.ingredients_name)&&convert(Number(lot.quantity),lot.unit,ingredient.unit,ingredient.ingredients_name)!==null);
    for(const lot of candidates){
      if(needed<=1e-9)break;
      const available=convert(Number(lot.quantity),lot.unit,ingredient.unit,ingredient.ingredients_name)!;
      const usedRecipe=Math.min(available,needed);
      const consumed=convert(usedRecipe,ingredient.unit,lot.unit,ingredient.ingredients_name)!;
      needed-=usedRecipe;lot.quantity=Number(lot.quantity)-consumed;
      updates.push({source:lot.source,id:lot.id,consumed:Number(consumed.toFixed(8))});
    }
  }
  return updates;
}

async function rows(table:string,query="select=*") {return (await db(`${table}?${query}`)).body||[]}
async function bundle(){
  const [products,leftovers,recipes,ingredients]=await Promise.all([
    rows("products","select=*&order=expiration_date.asc"),rows("leftovers","select=*&order=expiration_date.asc"),
    rows("recipes","select=*&order=name.asc"),rows("recipe_ingredients","select=*&order=id.asc")
  ]);
  const lots=buildLots(products,leftovers);const grouped=new Map<number,Row[]>();
  for(const ingredient of ingredients){const id=Number(ingredient.recipe_id);grouped.set(id,[...(grouped.get(id)||[]),ingredient])}
  const enriched=recipes.map((recipe:Row)=>{const list=grouped.get(Number(recipe.id))||[];return {...recipe,ingredients:list,availability:availability(list,lots)}});
  return {inventory:{items:lots,count:lots.length},recipes:{recipes:enriched,count:enriched.length},catalog:{products:PRODUCTS,units:[...new Set(Object.values(UNIT_ALIASES))].sort(),aliases:UNIT_ALIASES}};
}

function authorized(req:Request){
  const expected=env("APP_ACCESS_PIN");if(!expected)return true;
  const supplied=req.headers.get("x-caldero-pin")||"";
  const left=Buffer.from(supplied),right=Buffer.from(expected);
  return left.length===right.length&&timingSafeEqual(left,right);
}
function allowWrite(clientId:string){
  const now=Date.now(),current=writeWindows.get(clientId);
  if(!current||current.reset<=now){writeWindows.set(clientId,{count:1,reset:now+600000});return true}
  if(current.count>=30)return false;
  current.count+=1;return true;
}
async function payload(req:Request,fields:string[]){
  const length=Number(req.headers.get("content-length")||0);if(length>20000)throw new HttpError(413,"Solicitud demasiado grande.");
  let data:any;try{data=await req.json()}catch{throw new HttpError(400,"El cuerpo debe contener JSON válido.")}
  for(const field of fields)if(data?.[field]===undefined||data[field]===null||data[field]==="")throw new HttpError(400,`Falta el campo ${field}.`);
  return data;
}
function validDate(value:unknown){return /^\d{4}-\d{2}-\d{2}$/.test(String(value))&&!Number.isNaN(Date.parse(`${value}T00:00:00`))}

async function insertInventory(req:Request){
  const data=await payload(req,["name","category","quantity","unit","expiration_date"]);const quantity=Number(data.quantity);
  if(!(quantity>0)||!validDate(data.expiration_date))return response({error:"Cantidad o fecha inválida."},400);
  const item={name:String(data.name).trim(),category:String(data.category).trim(),quantity,unit:String(data.unit).trim(),expiration_date:data.expiration_date};
  const created=(await db("products",{method:"POST",headers:{Prefer:"return=representation"},body:JSON.stringify(item)})).body;
  return response({item:created?.[0]||item},201);
}
async function insertLeftover(req:Request){
  const data=await payload(req,["recipe_id","name","quantity","unit","expiration_date"]);const quantity=Number(data.quantity),recipeId=Number(data.recipe_id);
  if(!(quantity>0)||!Number.isInteger(recipeId)||!validDate(data.expiration_date))return response({error:"Cantidad, receta o fecha inválida."},400);
  const recipe=await rows("recipes",`select=id&id=eq.${recipeId}&limit=1`);if(!recipe.length)return response({error:"Receta no encontrada."},404);
  const item={recipe_id:recipeId,name:String(data.name).trim(),quantity,unit:String(data.unit).trim(),expiration_date:data.expiration_date};
  const created=(await db("leftovers",{method:"POST",headers:{Prefer:"return=representation"},body:JSON.stringify(item)})).body;
  return response({leftover:created?.[0]||item},201);
}
async function prepareRecipe(id:number){
  const [recipe,ingredients,products,leftovers]=await Promise.all([
    rows("recipes",`select=*&id=eq.${id}&limit=1`),rows("recipe_ingredients",`select=*&recipe_id=eq.${id}&order=id.asc`),
    rows("products","select=*&order=expiration_date.asc"),rows("leftovers","select=*&order=expiration_date.asc")
  ]);
  if(!recipe.length)return response({error:"Receta no encontrada."},404);
  const lots=buildLots(products,leftovers),status=availability(ingredients,lots);
  if(!status.can_prepare)return response({error:"Faltan ingredientes.",availability:status},409);
  const updates=consumptionPlan(ingredients,lots);
  const applied=(await db("rpc/apply_inventory_consumption",{method:"POST",body:JSON.stringify({p_updates:updates})})).body;
  return response({message:"Receta preparada; inventario actualizado.",recipe:recipe[0],updates:applied});
}

export default async (req:Request,context?:{ip?:string})=>{
  try{
    const path=new URL(req.url).pathname.replace(/^\/api\/?/,"");
    if(req.method==="GET"&&path==="health"){const data=await rows("products","select=id&limit=1");return response({status:"ok",supabase:"connected",products_visible:data.length})}
    if(req.method==="GET"&&(path==="bootstrap"||path===""))return response(await bundle());
    if(req.method!=="GET"&&!authorized(req))return response({error:"Código de acceso requerido o incorrecto."},401);
    if(req.method!=="GET"&&!allowWrite(context?.ip||req.headers.get("x-forwarded-for")||"unknown"))return response({error:"Demasiados intentos. Espera unos minutos."},429);
    if(req.method==="POST"&&path==="inventory")return await insertInventory(req);
    if(req.method==="POST"&&path==="leftovers")return await insertLeftover(req);
    const match=path.match(/^recipes\/(\d+)\/prepare$/);if(req.method==="POST"&&match)return await prepareRecipe(Number(match[1]));
    return response({error:"Ruta no encontrada."},404);
  }catch(error){console.error(error);if(error instanceof HttpError)return response({error:error.message},error.status);return response({error:"No se pudo completar la operación."},500)}
};
