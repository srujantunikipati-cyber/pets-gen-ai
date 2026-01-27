import { EmailTemplate } from "../model/emailTemplateSchema";

export class TemplateRepository {
  /**
   * Fetch template by name
   * @param templateName Name of the template
   */
  static async getTemplateByName(templateName: string) {
    return EmailTemplate.findOne({ name: templateName });
  }
}
