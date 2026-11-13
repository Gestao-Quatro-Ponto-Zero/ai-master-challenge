import asyncio, json
from playwright.async_api import async_playwright
URL="http://localhost:3000"
import os
URL=os.environ.get("URL",URL)
CASES=[("01_access_automatic","I cannot log into my account, my password expired and I need help to access the VPN."),
("02_refund_b2c_humano","I want a refund for my order, the product arrived broken and I was charged twice."),
("03_incidente_critico_escalate","Our entire network is down, nobody in the office can work, production systems are offline."),
("04_admin_rights_humano","I need admin access on my laptop to install software."),
("05_texto_curto_humano","help"),
("06_fora_escopo","Can you book a table for the company lunch on Friday?")]
async def main():
    log=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await b.new_page(viewport={"width":1440,"height":1000})
        for name,text in CASES:
            await pg.goto(URL,wait_until="networkidle")
            await pg.fill("textarea",text)
            async with pg.expect_response(lambda r:"/api/" in r.url and r.request.method=="POST",timeout=30000) as ri:
                await pg.get_by_role("button",name="Analisar Chamado").click()
            r=await ri.value
            body=await r.json()
            await pg.wait_for_timeout(1500)
            await pg.screenshot(path=f"{name}.png",full_page=True)
            log.append({"screenshot":f"{name}.png","input":text,"api_status":r.status,"response":body})
        for path,name in [("/metricas","07_pagina_metricas"),("/sobre","08_pagina_sobre")]:
            await pg.goto(URL+path,wait_until="networkidle"); await pg.wait_for_timeout(2000)
            await pg.screenshot(path=f"{name}.png",full_page=True)
            log.append({"screenshot":f"{name}.png","page":path})
        await b.close()
    json.dump(log,open("capture_log.json","w"),indent=2,ensure_ascii=False)
asyncio.run(main())
