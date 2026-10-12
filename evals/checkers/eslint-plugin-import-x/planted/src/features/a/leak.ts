// Planted violation: feature a imports feature b.
import { featureB } from "../b";

export const borrowed = featureB();
