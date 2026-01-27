import { EmailTemplate } from "../model/emailTemplateSchema";
import { logger } from "../utils/logger";
import { templates } from "../data/emailTemplates"; // adjust path
export async function seedTemplates() {
  for (const t of templates) {
    try {
      const existing = await EmailTemplate.findOne({ name: t.name });

      if (existing) {
        existing.type = t.type;
        existing.subject = t.subject;
        existing.htmlTemplate = t.htmlTemplate;
        existing.textTemplate = t.textTemplate || existing.textTemplate;
        existing.placeholders = t.placeholders;
        existing.updatedBy = t.createdBy;
        await existing.save();
        logger.info(`🔄 Updated template: ${t.name}`);
      } else {
        await EmailTemplate.create(t);
        logger.info(`✅ Created template: ${t.name}`);
      }
    } catch (err) {
      logger.error(`❌ Error processing template ${t.name}:`, err);
    }
  }
}
