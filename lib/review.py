# lib/review.py
from __init__ import CONN, CURSOR


class Review:
    # cache of Review instances by id
    all = {}

    def __init__(self, year, summary, employee, id=None):
        """
        `employee` can be:
        - an Employee instance, or
        - an integer employee_id
        """
        self.id = id
        self.year = year
        self.summary = summary
        self.employee = employee  # goes through the property setter

    def __repr__(self):
        return (
            f"<Review {self.id}: {self.year}, {self.summary}, "
            f"Employee {self.employee.id}>"
        )

    # -------------------
    # Property validation
    # -------------------
    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        if not isinstance(value, int):
            raise ValueError("year must be an integer")
        if value < 2000:
            raise ValueError("year must be >= 2000")
        self._year = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        if not isinstance(value, str) or len(value.strip()) == 0:
            raise ValueError("summary must be a non-empty string")
        self._summary = value

    @property
    def employee(self):
        return self._employee

    @employee.setter
    def employee(self, value):
        """
        Accept either:
        - an Employee instance, or
        - an integer employee_id
        """
        from employee import Employee

        if isinstance(value, Employee):
            if value.id is None:
                raise ValueError(
                    "employee must be persisted before assigning to review"
                )
            self._employee = value
        elif isinstance(value, int):
            employee = Employee.find_by_id(value)
            if not employee:
                raise ValueError(
                    "employee must be persisted before assigning to review"
                )
            self._employee = employee
        else:
            raise ValueError("employee must be an Employee instance")

    @property
    def employee_id(self):
        return self.employee.id if hasattr(self, "_employee") and self._employee else None

    @employee_id.setter
    def employee_id(self, value):
        from employee import Employee

        if not isinstance(value, int):
            raise ValueError("employee_id must be an integer")
        employee = Employee.find_by_id(value)
        if not employee:
            raise ValueError("employee_id must refer to a persisted Employee")
        self.employee = employee

    # -------------------
    # Table management
    # -------------------
    @classmethod
    def create_table(cls):
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        sql = "DROP TABLE IF EXISTS reviews;"
        CURSOR.execute(sql)
        CONN.commit()

    # -------------------
    # ORM methods
    # -------------------
    def save(self):
        """
        Persist this Review instance to the database.
        If it doesn't have an id yet, INSERT and set self.id.
        If it does, delegate to update().
        """
        if self.id is None:
            sql = """
                INSERT INTO reviews (year, summary, employee_id)
                VALUES (?, ?, ?);
            """
            CURSOR.execute(sql, (self.year, self.summary, self.employee.id))
            CONN.commit()

            self.id = CURSOR.lastrowid
            type(self).all[self.id] = self
        else:
            self.update()
        return self

    @classmethod
    def create(cls, year, summary, employee_id):
        """
        Create a new Review instance and save it.

        Tests call:
            Review.create(2023, "Excellent Python skills!", employee.id)
        """
        from employee import Employee

        employee = Employee.find_by_id(employee_id)
        if not employee:
            raise ValueError("employee_id must refer to a persisted Employee")

        # __init__ will run the validations on year and summary
        review = cls(year, summary, employee)
        review.save()
        return review

    @classmethod
    def instance_from_db(cls, row):
        """
        Given a database row, return a cached Review instance
        with attributes matching the row.
        """
        id, year, summary, employee_id = row

        review = cls.all.get(id)
        from employee import Employee

        employee = Employee.find_by_id(employee_id)

        if review:
            review.year = year
            review.summary = summary
            review.employee = employee
        else:
            review = cls(year, summary, employee, id=id)
            cls.all[id] = review

        return review

    @classmethod
    def find_by_id(cls, id):
        sql = "SELECT * FROM reviews WHERE id = ?;"
        row = CURSOR.execute(sql, (id,)).fetchone()
        if row:
            return cls.instance_from_db(row)
        return None

    def update(self):
        """
        Update the DB row corresponding to this Review instance.
        """
        sql = """
            UPDATE reviews
            SET year = ?, summary = ?, employee_id = ?
            WHERE id = ?;
        """
        CURSOR.execute(
            sql,
            (self.year, self.summary, self.employee.id, self.id),
        )
        CONN.commit()
        type(self).all[self.id] = self

    def delete(self):
        """
        Delete this Review from the DB and cache.
        """
        sql = "DELETE FROM reviews WHERE id = ?;"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()

        if self.id in type(self).all:
            del type(self).all[self.id]

        self.id = None

    @classmethod
    def get_all(cls):
        sql = "SELECT * FROM reviews;"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]
