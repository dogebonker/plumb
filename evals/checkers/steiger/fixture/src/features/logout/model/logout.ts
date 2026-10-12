import { type User, guest } from "../../../entities/user";

export function logout(_user: User): User {
  return guest;
}
