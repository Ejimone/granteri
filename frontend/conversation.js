import Vapi from "@vapi-ai/web";

const vapi = new Vapi("YOUR_PUBLIC_API_KEY");

// Start voice conversation
vapi.start(process.env.VAPI_API_KEY, {
  phoneNumberId: process.env.PHONE_NUMBER_ID,
  customer: { number: "+1234567890" },
  assistantId: process.env.ASSISTANT_ID,
});

// Listen for events
vapi.on("call-start", () => console.log("Call started"));
vapi.on("call-end", () => console.log("Call ended"));
vapi.on("message", (message) => {
  if (message.type === "transcript") {
    console.log(`${message.role}: ${message.transcript}`);
  }
});
