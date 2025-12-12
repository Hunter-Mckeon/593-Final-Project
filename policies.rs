use crate::policy::context::ContextData;
use mysql::prelude::Queryable;
use sesame::context::UnprotectedContext;
use sesame::policy::{Reason, SimplePolicy};
use sesame::SesameTypeOut;
use sesame_mysql::{schema_policy, SchemaPolicy};

// This policy applies to the answer column in the submissions table
#[schema_policy(table = "submissions", column = 3)]
#[derive(Clone)]
pub struct AccessControlPolicy {
    student_id: String,   // Keeps the value of the student id column from the table.
}

impl SimplePolicy for AccessControlPolicy {
    fn simple_name(&self) -> String {
        format!("AccessControlPolicy")
    }

    fn simple_check(&self, context: &UnprotectedContext, _reason: Reason) -> bool {
        type ContextDataOut = <ContextData as SesameTypeOut>::Out;
        let context: &ContextDataOut = context.downcast_ref().unwrap();

        // The user trying to view the submission.
        let user: &String = &context.user_email;
        user == &self.student_id || user == "admin@bu.edu"
    }

    fn simple_join_direct(&mut self, other: &mut Self) {
        if self.student_id != other.student_id {
            self.student_id = String::from("");
        }
    }
}

impl SchemaPolicy for AccessControlPolicy {
    fn from_row(table_name: &str, row: &Vec<mysql::Value>) -> Self
    where
        Self: Sized,
    {
        assert_eq!(table_name, "submissions");
        AccessControlPolicy {
            // Read the value of the student_id column from the submissions table.
            student_id: mysql::from_value(row[1].clone()),
        }
    }
}
