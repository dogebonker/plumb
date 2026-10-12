import { button } from "../../../shared/ui";
import { login } from "../../../features/login";
import { logout } from "../../../features/logout";

export function profilePage(): string {
  return button(login("bob").name) + button(logout(login("bob")).name);
}
