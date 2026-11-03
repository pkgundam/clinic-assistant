-- Queries for looking at the clinic data in Neon's SQL editor.
-- Voided rows (void_sw = true) count as deleted, so every query skips them.
-- Times are shown in clinic time (America/Los_Angeles).

-- 1. All users with their insurance plan
select u.id,
       u.role,
       u.full_name,
       u.email,
       u.phone,
       u.date_of_birth,
       p.name  as insurance_plan,
       p.accepted as plan_accepted,
       u.insurance_member_id
from users u
left join insurance_plans p on p.id = u.insurance_plan_id and not p.void_sw
where not u.void_sw
order by u.id;

-- 2. All doctors
select id, full_name, speciality_code, speciality
from doctors
where not void_sw
order by full_name;

-- 3. Dr. Anita Rao's open slots this week (from now until the end of Sunday)
select c.id,
       d.full_name,
       c.starts_at at time zone 'America/Los_Angeles' as starts_at_clinic_time,
       c.ends_at   at time zone 'America/Los_Angeles' as ends_at_clinic_time
from doctor_calendar c
join doctors d on d.id = c.doctor_id and not d.void_sw
where not c.void_sw
  and d.full_name = 'Dr. Anita Rao'
  and c.status = 'open'
  and c.starts_at >= now()
  and c.starts_at < (date_trunc('week', now() at time zone 'America/Los_Angeles') + interval '1 week')
                    at time zone 'America/Los_Angeles'
order by c.starts_at;

-- 4. All appointments with patient name, doctor name and slot time
select a.booking_code,
       u.full_name as patient,
       d.full_name as doctor,
       c.starts_at at time zone 'America/Los_Angeles' as slot_start_clinic_time,
       c.ends_at   at time zone 'America/Los_Angeles' as slot_end_clinic_time,
       a.reason,
       a.status
from user_appointments a
join users u           on u.id = a.user_id      and not u.void_sw
join doctor_calendar c on c.id = a.calendar_id  and not c.void_sw
join doctors d         on d.id = c.doctor_id    and not d.void_sw
where not a.void_sw
order by c.starts_at;
