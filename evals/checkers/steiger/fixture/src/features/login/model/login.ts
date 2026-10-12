import { type User, guest } from "../../../entities/user";

export function login(name: string): User {
  return name ? { id: name, name } : guest;
}
