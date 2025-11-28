frappe.listview_settings['Book Transaction'] = {
    add_fields: ["transaction_status"],

    get_indicator(doc) {
        const status = doc.transaction_status;

        if (status === "Returned") return ["Returned", "green", "transaction_status,=,Returned"];
        if (status === "Late Return") return ["Late Return", "red", "transaction_status,=,Late Return"];
        if (status === "Late") return ["Late", "orange", "transaction_status,=,Late"];
        return ["Issued", "blue", "transaction_status,=,Issued"];
    }
};
