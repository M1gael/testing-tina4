<?php
/**
 * Drives Crud::getDataTablesFilter() on whichever tree is passed as argv[1] and,
 * for each case, prints the SQL fragments it returns and whether a caller can
 * concatenate them into a working statement.
 *
 * This is a correctness probe, not an attack. The question is narrow: does a
 * value or a name that arrived from the request reach the SQL text verbatim?
 * The canonical way to see that is a legitimate name with an apostrophe
 * (O'Brien): if the value is quoted correctly the row is found, and if it is
 * pasted raw between single quotes the statement is malformed and errors. Same
 * for a column the ORM does not have, and a sort direction that is not asc/desc.
 *
 * Verdict per case is "how many of the 3 people came back", or the SQL error.
 *
 * Usage: php drive.php /path/to/tree
 */

$root = rtrim($argv[1] ?? '', '/');
require $root . '/vendor/autoload.php';

use Tina4\Crud;
use Tina4\DataSQLite3;
use Tina4\ORM;

class Person extends ORM
{
    public $id;
    public $firstName;
    public $email;
    public $primaryKey = "id";
    public $tableName = "people";
}

/** A fresh table per case, so one case cannot see another's state. */
function freshDatabase(): SQLite3
{
    $database = new SQLite3(":memory:");
    $database->exec("create table people (id integer, first_Name text, email text)");
    $database->exec("insert into people values (1, 'Ann',     'ann@example.com')");
    $database->exec("insert into people values (2, 'Bob',     'bob@example.com')");
    $database->exec("insert into people values (3, \"O'Brien\", 'obrien@example.com')");
    return $database;
}

/**
 * What the method's own docblock says a caller does: "an array of dataTables
 * style filters for use in your queries". Build the query and run it.
 */
function runAsCaller(array $filter): array
{
    $database = freshDatabase();

    $sql = "select id from people t";
    if ($filter["where"] !== "") {
        $sql .= " where " . $filter["where"];
    }
    if ($filter["orderBy"] !== "") {
        $sql .= " order by " . $filter["orderBy"];
    }
    $sql .= " limit " . $filter["length"] . " offset " . $filter["start"];

    $result = @$database->query($sql);
    if ($result === false) {
        return ["sql" => $sql, "error" => $database->lastErrorMsg(), "ids" => null];
    }
    $ids = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $ids[] = $row["id"];
    }
    return ["sql" => $sql, "error" => null, "ids" => $ids];
}

function drive(string $name, array $request, bool $withConnection = true): void
{
    $orm = new Person();
    if ($withConnection) {
        $orm->DBA = new DataSQLite3(":memory:");
    }

    $_REQUEST = $request;
    $filter = Crud::getDataTablesFilter("t.", $orm);
    $_REQUEST = [];

    echo "--- {$name}\n";
    echo "  where   : " . var_export($filter["where"], true) . "\n";
    echo "  orderBy : " . var_export($filter["orderBy"], true) . "\n";

    $outcome = runAsCaller($filter);
    if ($outcome["error"] !== null) {
        echo "  run     : SQL ERROR: " . $outcome["error"] . "\n";
    } else {
        echo "  run     : rows [" . implode(",", $outcome["ids"]) . "] (" . count($outcome["ids"]) . " of 3)\n";
    }
    echo "  sql     : " . $outcome["sql"] . "\n";
}

$searchable = [
    ["data" => "firstName", "searchable" => "true"],
    ["data" => "email",     "searchable" => "true"],
];

echo "tree: {$root}\n";
echo "tina4php: " . trim(shell_exec("git -C " . escapeshellarg($root) . " log --oneline -1 2>/dev/null") ?? "?") . "\n\n";

// 1. Ordinary search: one of three people is Ann.
drive("A: search 'ann'", [
    "columns" => $searchable,
    "search"  => ["value" => "ann"],
]);

// 2. A legitimate name that contains a single quote. Person 3 is O'Brien.
//    Correct quoting finds the row; raw concatenation makes a broken statement.
drive("B: search for the name O'Brien", [
    "columns" => $searchable,
    "search"  => ["value" => "O'Brien"],
]);

// 3. A column the ORM does not define. The request names the sortable/searchable
//    column, so this asks whether an unknown name reaches the statement.
drive("C: sort by a column the model has no field for", [
    "columns" => [["data" => "no_such_column", "searchable" => "true"]],
    "order"   => [["column" => 0, "dir" => "asc"]],
]);

// 4. A sort direction that is not asc or desc.
drive("D: sort direction that is not asc/desc", [
    "columns" => $searchable,
    "order"   => [["column" => 0, "dir" => "nonsense"]],
]);

// 5. The same honest search, but the ORM has no database connection bound.
drive("E: search 'ann' with no connection bound", [
    "columns" => $searchable,
    "search"  => ["value" => "ann"],
], false);
