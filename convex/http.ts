import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";
const http=httpRouter();
http.route({path:"/ingest",method:"POST",handler:httpAction(async(ctx,req)=>{const secret=process.env.INGEST_SECRET;if(!secret||req.headers.get("x-ingest-secret")!==secret)return new Response("unauthorized",{status:401});const data=await req.json();const id=await ctx.runMutation(api.entries.ingest,data);return Response.json({ok:true,id});})});
export default http;
