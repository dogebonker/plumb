import { button } from "../../../shared/ui";
import { login } from "../../../features/login";
import { logout } from "../../../features/logout";

export function homePage(): string {
  return button(logout(login("ann")).name);
}
