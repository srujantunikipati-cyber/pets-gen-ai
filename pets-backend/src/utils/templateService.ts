import { TemplateRepository } from "../repository/EmailTemplateRepository";

export interface PlaceholderMap {
  [key: string]: string; // e.g. { USERNAME: "John", RESET_LINK: "https://..." }
}

export class TemplateService {
  /**
   * Fetch template by name, replace placeholders, and return processed content
   * @param templateName Name of the template
   * @param placeholders Object with placeholder values
   */
  static async renderTemplate(templateName: string, placeholders: PlaceholderMap) {
    const template = await TemplateRepository.getTemplateByName(templateName);

    if (!template) {
      throw new Error(`Template "${templateName}" not found`);
    }

    let html = template.htmlTemplate || "";
    let text = template.textTemplate || "";

    // Replace all placeholders in both html and text
    for (const key of template.placeholders) {
      const value = placeholders[key] || "";
      const regex = new RegExp(`{{${key}}}`, "g");
      html = html.replace(regex, value);
      text = text.replace(regex, value);
    }

    return { subject: template.subject, html, text };
  }
}
