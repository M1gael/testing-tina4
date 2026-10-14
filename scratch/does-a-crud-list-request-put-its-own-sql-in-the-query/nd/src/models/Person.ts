import { BaseModel } from "@tina4/orm";
export default class Person extends BaseModel {
  static tableName = "people";
  static fields = {
    id:   { type: "integer" as const, primaryKey: true, autoIncrement: true },
    name: { type: "string" as const },
    age:  { type: "integer" as const },
  };
}
