/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CustomDiscountLimitPopup extends Component {
    static template = "pos_discount_restrict_omax.CustomDiscountLimitPopup";
    static components = { Dialog };

    static props = {
        confirm: { type: Function, optional: true },
        close: { type: Function, optional: true },
        cancel: { type: Function, optional: true },
        title: { type: String, optional: true },
        body: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            password: ""
        });
        this.passwordInputRef = useRef("passwordInput");
    }

    mounted() {
        if (this.passwordInputRef.el) {
            this.passwordInputRef.el.focus();
        }
    }

    onPasswordChange(ev) {
        this.state.password = ev.target.value;
    }

    onKeyDown(ev) {
        if (ev.key === 'Enter') {
            this.onConfirm();
        }
    }

    async onConfirm() {
        const password = this.state.password;
        
        if (!password.trim()) {
            return;
        }
        
        if (this.props.confirm) {
            await this.props.confirm(password);
        }
        
        if (this.props.close) {
            this.props.close();
        }
    }

    onClose() {
        if (this.props.cancel) {
            this.props.cancel();
        }
        
        if (this.props.close) {
            this.props.close();
        }
    }
}