import { validateEmail } from "./validators";

export function loginUser(email, password) {
    if (!validateEmail(email)) {
        return { success: false, error: "Invalid email" };
    }
    return { success: true, token: "abc123" };
}

class AuthService {
    constructor() {
        this.users = [];
    }

    register(user) {
        this.users.push(user);
    }
}
