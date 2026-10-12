// Planted violation: domain imports a driven adapter.
import { now } from "../adapters/out/clock/clock";

export const createdAt = now();
