// Copyright (c) 2024, Sufyan and contributors
// For license information, please see license.txt


var directory_response;


frappe.ui.form.on("Lenel Site Setting", {
	
    
    
    
    refresh: async function(frm) {

        let button = frm.add_custom_button('Execute', async () => {
        
            let directory_respnse = null;
            let session_token = null;
            let logged_events = null;
    
            if( frm.doc.user_name && frm.doc.password && frm.doc.application_id && frm.doc.api && frm.doc.host_ip && frm.doc.port && frm.doc.directory_id && frm.doc.employee_id_field && frm.doc.logtype_field && frm.doc.logtype_definition && frm.doc.timestamp_field )
            {
    
                await frappe.call({
                    method: "lenel.lenel.api.api.authentication",
                    args: {
                        api : frm.doc.api ,
                        host_ip : frm.doc.host_ip ,
                        port : frm.doc.port ,
                        application_id : frm.doc.application_id ,
                        user_name : frm.doc.user_name ,
                        password : frm.doc.password ,
                        directory_id : frm.doc.directory_id ,
                        tls : frm.doc.og_openaccess_tls ,
    
                    },
                    freeze: true,
                    callback: function (r) {
                        if (r.message) {
                            session_token = r.message.session_token;
                        }
                    },
                });
    
    
                let till_datetime = "False";
                if (frm.doc.till_datetime)
                {
                    till_datetime = frm.doc.till_datetime ;
                }
    
                let logs_array = [] ;
                let inout = [];
                for( let row of frm.doc.logtype_definition)
                { logs_array.push(row.lenel_definition);
                  inout.push(row.logtype);  
                }
    
                let utc_time = 0 ;
                if (frm.doc.time_zone)
                {
                    utc_time = parseInt(frm.doc.time_zone) ;
                }
    
    
                await frappe.call({
                    method: "lenel.lenel.api.api.get_logged_events",
                    args: {
                        api : frm.doc.api ,
                        host_ip : frm.doc.host_ip ,
                        port : frm.doc.port ,
                        application_id : frm.doc.application_id ,
                        user_name : frm.doc.user_name ,
                        password : frm.doc.password ,
                        tls : frm.doc.og_openaccess_tls ,
                        session_token : session_token ,
                        from_date : till_datetime ,
                        device_id : frm.doc.employee_id_field ,
                        log_type : frm.doc.logtype_field ,
                        timestamp : frm.doc.timestamp_field ,
                        table : logs_array ,
                        inout : inout ,
                        utc_time : utc_time
                    },
                    freeze: true,
                    callback: function (r) {
                        if (r.message) {
                            cur_time = r.message;
                        }
                    },
                });
    
                frm.set_value("till_datetime",cur_time);
                frm.save();
            
            }
            else 
            {
                frappe.msgprint("First Enter above Mandatory Fields.");
            }




        });
        
        $(button).css({
            'background-color': 'black',
            'color': 'white',
            'border-color': 'black'
        });
    },

    // scheduler : async function(frm)
    // {
    //     await frappe.call({
    //         method: "lenel.lenel.api.api.get_checkins_from_scheduler",
    //         args : {
    //         },
    //         callback : function(r) {
    //             if (r.message) {
    //                 var cur_time = r.message;
    //             }
    //         },
    //     });
    // },


    // get_checkins : async function(frm)
    // {
    // },


});
