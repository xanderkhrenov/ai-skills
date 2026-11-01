import { generateApi } from "swagger-typescript-api";

const [input, output] = process.argv.slice(2);
await generateApi({
  input,
  output,
  httpClientType: "fetch",
  modular: true,
  moduleNameFirstTag: true,
  generateClient: true,
  silent: true,
});
