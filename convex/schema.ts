import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";
export default defineSchema({
  entries: defineTable({
    externalId:v.string(), kind:v.union(v.literal("official_alert"),v.literal("news")),
    title:v.string(), summary:v.string(), url:v.string(), sourceName:v.string(), sourceDomain:v.string(),
    isOfficial:v.boolean(), province:v.union(v.literal("Madrid"),v.literal("Ávila"),v.literal("Toledo")),
    town:v.optional(v.string()), publishedAt:v.number(), ingestedAt:v.number(),
    incidentKey:v.optional(v.string()), contentHash:v.string(), rawText:v.optional(v.string()),
    verification:v.union(v.literal("official"),v.literal("whitelisted_media"),v.literal("rejected"))
  }).index("by_externalId",["externalId"]).index("by_kind_and_publishedAt",["kind","publishedAt"]).index("by_province_and_publishedAt",["province","publishedAt"]).index("by_contentHash",["contentHash"]),
  sources: defineTable({name:v.string(),domain:v.string(),url:v.string(),type:v.union(v.literal("official"),v.literal("media")),enabled:v.boolean(),province:v.optional(v.string())}).index("by_domain",["domain"]),
});
