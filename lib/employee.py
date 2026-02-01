# lib/employee.py
from __init__ import CURSOR, CONN
from department import Department


class Employee:
    # cache of Employee instances by id
    all = {}

    def __init__(self, name, job_title, department_id, id=None):
        self.id = id
        self.name = name
        self.job_title = job_title
        self.department_id = department_id

    def __repr__(self):
        return (
            f"<Employee {self.id}: {self.name}, {self.job_title}, "
            f"Department ID: {self.department_id}>"
        )

    # -------------------
    # Property validation
    # -------------------
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if isinstance(name, str) and len(name):
            self._name = name
        else:
            raise ValueError("Name must be a non-empty string")

    @property
    def job_title(self):
        return self._job_title

    @job_title.setter
    def job_title(self, job_title):
        if isinstance(job_title, str) and len(job_title):
            self._job_title = job_title
        else:
            raise ValueError("job_title must be a non-empty string")

    @property
    def department_id(self):
        return self._department_id

    @department_id.setter
    def department_id(self, department_id):
        if isinstance(department_id, int) and Department.find_by_id(department_id):
            self._department_id = department_id
        else:
            raise ValueError(
                "department_id must reference a department in the database"
            )

    # -------------------
    # Table management
    # -------------------
    @classmethod
    def create_table(cls):
        """Create a new table to persist the attributes of Employee instances."""
        sql = """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                job_title TEXT,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            );
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        """Drop the table that persists Employee instances."""
        sql = "DROP TABLE IF EXISTS employees;"
        CURSOR.execute(sql)
        CONN.commit()

    # -------------------
    # ORM methods
    # -------------------
    def save(self):
        """
        Insert a new row with the name, job_title, and department_id of
        the current Employee object. Set id and cache in Employee.all.
        """
        if self.id is None:
            sql = """
                INSERT INTO employees (name, job_title, department_id)
                VALUES (?, ?, ?);
            """
            CURSOR.execute(sql, (self.name, self.job_title, self.department_id))
            CONN.commit()

            self.id = CURSOR.lastrowid
            type(self).all[self.id] = self
        else:
            self.update()
        return self

    def update(self):
        """Update the table row corresponding to the current Employee instance."""
        sql = """
            UPDATE employees
            SET name = ?, job_title = ?, department_id = ?
            WHERE id = ?;
        """
        CURSOR.execute(
            sql, (self.name, self.job_title, self.department_id, self.id)
        )
        CONN.commit()
        type(self).all[self.id] = self

    def delete(self):
        """
        Delete the table row corresponding to the current Employee instance,
        remove from cache, and clear id.
        """
        sql = "DELETE FROM employees WHERE id = ?;"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()

        if self.id in type(self).all:
            del type(self).all[self.id]

        self.id = None

    @classmethod
    def create(cls, name, job_title, department_id):
        """Initialize a new Employee instance and save it to the database."""
        employee = cls(name, job_title, department_id)
        employee.save()
        return employee

    @classmethod
    def instance_from_db(cls, row):
        """
        Given a db row, return a cached Employee instance with matching attributes.
        """
        id, name, job_title, department_id = row

        employee = cls.all.get(id)
        if employee:
            employee.name = name
            employee.job_title = job_title
            employee.department_id = department_id
        else:
            employee = cls(name, job_title, department_id, id=id)
            cls.all[id] = employee

        return employee

    @classmethod
    def get_all(cls):
        """Return a list containing one Employee object per table row."""
        sql = "SELECT * FROM employees;"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]

    @classmethod
    def find_by_id(cls, id):
        """Return Employee corresponding to row with given id, or None."""
        sql = "SELECT * FROM employees WHERE id = ?;"
        row = CURSOR.execute(sql, (id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def find_by_name(cls, name):
        """Return first Employee with the given name, or None."""
        sql = "SELECT * FROM employees WHERE name = ?;"
        row = CURSOR.execute(sql, (name,)).fetchone()
        return cls.instance_from_db(row) if row else None

    # -------------------
    # Relationship helper
    # -------------------
    def reviews(self):
        """
        Return a list of Review instances associated with this Employee.
        """
        from review import Review  # avoid circular import at module load time

        sql = "SELECT * FROM reviews WHERE employee_id = ?;"
        rows = CURSOR.execute(sql, (self.id,)).fetchall()
        return [Review.instance_from_db(row) for row in rows]
