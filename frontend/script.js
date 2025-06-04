import { VapiClient } from "@vapi-ai/server-sdk";

const vapi = new VapiClient({
  token: process.env.VAPI_API_KEY,
});

// Create an outbound call
const call = await vapi.calls.create({
  phoneNumberId: process.env.PHONE_NUMBER_ID,
  customer: { number: "+1234567890" },
  assistantId: process.env.ASSISTANT_ID,
});

console.log(`Call created: ${call.id}`);
