import { toCrud } from "@tina4/orm";
import Person from "../../models/Person.ts";
export default async function (req: any, res: any) {
  return res.html(await toCrud(req, { model: Person as any, public: true }));
}
