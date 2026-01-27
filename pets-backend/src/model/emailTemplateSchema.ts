import { Schema, model, Document } from "mongoose";

export interface IEmailTemplate extends Document {
  name: string;                        // unique name of template
  type: string;                        // e.g. password_reset, welcome, otp
  subject: string;                     // email subject
  htmlTemplate: string;                // HTML body
  textTemplate?: string;               // optional plain text body
  placeholders: string[];              // list of allowed dynamic variables
  createdBy: string;                   // userId or adminId
  updatedBy?: string;
  createdAt: Date;
  updatedAt: Date;
}

const EmailTemplateSchema = new Schema<IEmailTemplate>(
  {
    name: { type: String, required: true, unique: true },
    type: { type: String, required: true }, // e.g. password_reset, welcome
    subject: { type: String, required: true },

    htmlTemplate: { type: String, required: true },
    textTemplate: { type: String },

    placeholders: {
      type: [String],
      default: []
    },

    createdBy: { type: String, required: true },
    updatedBy: { type: String },
  },
  {
    timestamps: true, // auto adds createdAt & updatedAt
  }
);

export const EmailTemplate = model<IEmailTemplate>("EmailTemplate", EmailTemplateSchema);
