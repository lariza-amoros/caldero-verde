import test from "node:test";
import assert from "node:assert/strict";
import apiHandler, { availability, convert, namesMatch, normalize } from "../netlify/functions/api.ts";

test("normaliza nombres en español",()=>assert.equal(normalize("  Plátanos "),"platanos"));
test("convierte libras de arroz a tazas",()=>assert.ok(Math.abs(convert(1,"lb","taza","Arroz")-2.45185)<0.0001));
test("reutiliza una sobra como ingrediente",()=>{
  const result=availability([{ingredients_name:"Arroz",quantity:1,unit:"taza"}],[{name:"Arroz",quantity:1,unit:"taza",expired:false}]);
  assert.equal(result.can_prepare,true);
});
test("rechaza unidades incompatibles",()=>{
  const result=availability([{ingredients_name:"Arroz",quantity:1,unit:"unidad"}],[{name:"Arroz",quantity:1,unit:"lb",expired:false}]);
  assert.equal(result.missing[0].reason,"incompatible_unit");
});
test("acepta variaciones comunes del nombre",()=>assert.equal(namesMatch("Tomate","Tomates"),true));

test("protege escrituras cuando el PIN está configurado",async()=>{
  globalThis.Netlify={env:{get:name=>name==="APP_ACCESS_PIN"?"246810":"configured"}};
  const response=await apiHandler(new Request("https://caldero.test/api/inventory",{method:"POST",headers:{"content-type":"application/json"},body:"{}"}));
  assert.equal(response.status,401);
});

test("no revela errores internos del proveedor",async()=>{
  globalThis.Netlify={env:{get:name=>name==="SUPABASE_URL"?"https://example.supabase.co":"configured"}};
  const originalFetch=globalThis.fetch;
  const originalError=console.error;
  console.error=()=>{};
  globalThis.fetch=async()=>new Response(JSON.stringify({message:"internal database detail"}),{status:500,headers:{"content-type":"application/json"}});
  const result=await apiHandler(new Request("https://caldero.test/api/bootstrap"));
  const body=await result.json();
  globalThis.fetch=originalFetch;
  console.error=originalError;
  assert.equal(result.status,500);
  assert.equal(body.error,"No se pudo completar la operación.");
});
