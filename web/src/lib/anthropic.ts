import Anthropic from "@anthropic-ai/sdk";
import { promises as fs } from "fs";
import path from "path";

const DEFAULT_API_KEY = "YOUR_API_KEY";
const DEFAULT_BASE_URL = "YOUR_BASE_URL";
const DEFAULT_MODEL = "claude-sonnet-4-6";

const SETTINGS_PATH = path.join(process.cwd(), "..", "data", "api_settings.json");

interface ApiSettings {
  api_key?: string;
  base_url?: string;
  model?: string;
}

let _cachedSettings: ApiSettings | null = null;

async function loadApiSettings(): Promise<ApiSettings> {
  if (_cachedSettings) return _cachedSettings;
  try {
    const raw = await fs.readFile(SETTINGS_PATH, "utf-8");
    _cachedSettings = JSON.parse(raw);
    return _cachedSettings!;
  } catch {
    return {};
  }
}

export async function saveApiSettings(settings: ApiSettings) {
  const dir = path.dirname(SETTINGS_PATH);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(SETTINGS_PATH, JSON.stringify(settings, null, 2), "utf-8");
  _cachedSettings = settings;
}

export async function getApiSettings(): Promise<ApiSettings> {
  return loadApiSettings();
}

function resolveToken(): { token: string; baseURL: string } {
  // Priority: env vars > defaults
  const token =
    process.env.ANTHROPIC_AUTH_TOKEN ||
    process.env.ANTHROPIC_API_KEY ||
    DEFAULT_API_KEY;

  const baseURL =
    process.env.ANTHROPIC_BASE_URL ||
    DEFAULT_BASE_URL;

  return { token, baseURL };
}

export function createAnthropicClient(): Anthropic {
  const { token, baseURL } = resolveToken();

  // Standard Anthropic keys use x-api-key header
  if (token.startsWith("sk-ant-")) {
    return new Anthropic({ apiKey: token, authToken: null, baseURL });
  }

  // Proxy/custom keys use Bearer auth
  return new Anthropic({
    authToken: token,
    apiKey: null,
    baseURL,
  } as ConstructorParameters<typeof Anthropic>[0]);
}

export async function createAnthropicClientWithSettings(): Promise<{
  client: Anthropic;
  model: string;
}> {
  const settings = await loadApiSettings();

  const token =
    settings.api_key ||
    process.env.ANTHROPIC_AUTH_TOKEN ||
    process.env.ANTHROPIC_API_KEY ||
    DEFAULT_API_KEY;

  const baseURL =
    settings.base_url ||
    process.env.ANTHROPIC_BASE_URL ||
    DEFAULT_BASE_URL;

  const model = settings.model || DEFAULT_MODEL;

  let client: Anthropic;
  if (token.startsWith("sk-ant-")) {
    client = new Anthropic({ apiKey: token, authToken: null, baseURL });
  } else {
    client = new Anthropic({
      authToken: token,
      apiKey: null,
      baseURL,
    } as ConstructorParameters<typeof Anthropic>[0]);
  }

  return { client, model };
}
