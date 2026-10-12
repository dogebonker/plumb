// Planted violation: an entity imports a feature, a higher layer.
import { login } from "../../../features/login";

export const admin = login("admin");
