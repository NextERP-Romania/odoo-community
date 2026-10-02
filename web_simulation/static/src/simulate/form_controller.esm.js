// Copyright (C) 2026 NextERP Romania SRL
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

import {onWillStart} from "@odoo/owl";
import {FormController} from "@web/views/form/form_controller";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {user} from "@web/core/user";

const GROUP = "web_simulation.group_simulation";

patch(FormController.prototype, {
    setup() {
        super.setup();
        // A plain property is enough: onWillStart resolves before the
        // first render, and the cog menu is built later still.  Odoo 20's
        // OWL no longer exports useState.
        this.canSimulate = false;
        onWillStart(async () => {
            this.canSimulate = await user.hasGroup(GROUP);
        });
    },

    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems();
        items.webSimulation = {
            isAvailable: () => this.canSimulate,
            sequence: 35,
            icon: "play_arrow",
            description: _t("Simulate"),
            callback: () => this.simulateRecord(),
        };
        return items;
    },

    async simulateRecord() {
        const record = this.model.root;
        let args = null;
        if (record.isNew) {
            // Never saved: the form's values travel to the server, which
            // builds the record inside the savepoint it then throws away.
            args = [this.props.resModel, false, await record.getChanges()];
        } else {
            // The server reads the stored record, so pending edits have to
            // reach the database first.
            const saved = await record.save();
            if (!saved) {
                return;
            }
            args = [this.props.resModel, record.resId];
        }
        const action = await this.orm.call("web.simulation.run", "action_open", args);
        await this.actionService.doAction(action);
    },
});
