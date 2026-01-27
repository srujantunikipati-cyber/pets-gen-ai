import CryptoJS from "crypto-js";
import { logger } from "./logger";

const ENCRYPTION_KEY = process.env.CHAT_ENCRYPTION_KEY || "default-secret-key-change-in-production";

if (ENCRYPTION_KEY === "default-secret-key-change-in-production") {
    logger.warn("⚠️ Using default encryption key. Please set CHAT_ENCRYPTION_KEY in production!");
}

export interface EncryptedData {
    encrypted: string;
    iv: string;
}

/**
 * Encrypts a message using AES-256-GCM
 * @param plaintext - The message to encrypt
 * @returns Encrypted data with IV
 */
export function encryptMessage(plaintext: string): EncryptedData {
    try {
        const encrypted = CryptoJS.AES.encrypt(plaintext, ENCRYPTION_KEY).toString();

        // Extract IV from the encrypted string (CryptoJS includes it)
        const iv = CryptoJS.lib.WordArray.random(128 / 8).toString();

        return {
            encrypted,
            iv,
        };
    } catch (error: any) {
        logger.error(`❌ Encryption error: ${error.message}`);
        throw new Error("Failed to encrypt message");
    }
}

/**
 * Decrypts a message using AES-256-GCM
 * @param encrypted - The encrypted message
 * @param iv - Initialization vector (not used in crypto-js but kept for compatibility)
 * @returns Decrypted plaintext
 */
export function decryptMessage(encrypted: string, iv?: string): string {
    try {
        const bytes = CryptoJS.AES.decrypt(encrypted, ENCRYPTION_KEY);
        const decrypted = bytes.toString(CryptoJS.enc.Utf8);

        if (!decrypted) {
            throw new Error("Decryption resulted in empty string");
        }

        return decrypted;
    } catch (error: any) {
        logger.error(`❌ Decryption error: ${error.message}`);
        throw new Error("Failed to decrypt message");
    }
}

/**
 * Validates message content before encryption
 * @param content - Message content to validate
 * @returns true if valid, throws error otherwise
 */
export function validateMessageContent(content: string): boolean {
    const MAX_MESSAGE_LENGTH = 5000;

    if (!content || content.trim().length === 0) {
        throw new Error("Message content cannot be empty");
    }

    if (content.length > MAX_MESSAGE_LENGTH) {
        throw new Error(`Message exceeds maximum length of ${MAX_MESSAGE_LENGTH} characters`);
    }

    return true;
}

/**
 * Sanitizes message content to prevent XSS
 * @param content - Message content to sanitize
 * @returns Sanitized content
 */
export function sanitizeMessageContent(content: string): string {
    // Basic XSS prevention - remove HTML tags
    return content
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#x27;")
        .replace(/\//g, "&#x2F;");
}
