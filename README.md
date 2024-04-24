# django-state-manager

## Description

django-state-manager is based on [django-fsm](https://github.com/viewflow/django-fsm/tree/2.8.2) and provides 
implementation of states and transitions for Django models.

Additionally, it provides the coditions framework for implementing contitions for actions in an easy declarative way.

## Installation

```bash
pip install django-state-manager
```

## Finite state machine (FSM)

### Adding states to your model

Add FSMState field to your model

```python
from django_state_manager.fsm import FSMField, transition

class BlogPost(models.Model):
    state = FSMField(default='new')
```

Use the `transition` decorator to annotate model methods

```
@transition(field=state, source='new', target='published')
def publish(self):
    """
    This function may contain side-effects,
    like updating caches, notifying users, etc.
    The return value will be discarded.
    """
```

The `field` parameter accepts both a string attribute name or an
actual field instance.

If calling `publish()` succeeds without raising an exception, the state
field will be changed, but not written to the database.

```
from django_state_manager.fsm import can_proceed

def publish_view(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    if not can_proceed(post.publish):
        raise PermissionDenied

    post.publish()
    post.save()
    return redirect('/')
```
If some conditions are required to be met before changing the state, use
the `conditions` argument to `transition`. `conditions` must be a
list of functions taking one argument, the model instance. The function
must return either `True` or `False` or a value that evaluates to
`True` or `False`. If all functions return `True`, all conditions
are considered to be met and the transition is allowed to happen. If one
of the functions returns `False`, the transition will not happen.
These functions should not have any side effects.

You can use ordinary functions

```
def can_publish(instance):
    # No publishing after 17 hours
    if datetime.datetime.now().hour > 17:
        return False
    return True
```
Or model methods

```
def can_destroy(self):
    return self.is_under_investigation()
```
Use the conditions like this:
```
@transition(field=state, source='new', target='published', conditions=[can_publish])
def publish(self):
    """
    Side effects galore
    """

@transition(field=state, source='*', target='destroyed', conditions=[can_destroy])
def destroy(self):
    """
    Side effects galore
    """
```

You can instantiate a field with `protected=True` option to prevent
direct state field modification.

```
class BlogPost(models.Model):
    state = FSMField(default='new', protected=True)

model = BlogPost()
model.state = 'invalid' # Raises AttributeError
```
Note that calling
[refresh_from_db](https://docs.djangoproject.com/en/4.2/ref/models/instances/#django.db.models.Model.refresh_from_db)
on a model instance with a protected FSMField will cause an exception.

### `source` state

`source` parameter accepts a list of states, or an individual state or `django_state_manager.fsm.State` implementation.

You can use `*` for `source` to allow switching to `target` from any state. 

You can use `+` for `source` to allow switching to `target` from any state excluding `target` state.

### `target` state

`target` state parameter could point to a specific state or `django_state_manager.fsm.State` implementation

```          
from django_state_manager.fsm import FSMField, transition, RETURN_VALUE, GET_STATE
@transition(field=state,
            source='*',
            target=RETURN_VALUE('for_moderators', 'published'))
def publish(self, is_public=False):
    return 'for_moderators' if is_public else 'published'

@transition(
    field=state,
    source='for_moderators',
    target=GET_STATE(
        lambda self, allowed: 'published' if allowed else 'rejected',
        states=['published', 'rejected']))
def moderate(self, allowed):
    pass

@transition(
    field=state,
    source='for_moderators',
    target=GET_STATE(
        lambda self, **kwargs: 'published' if kwargs.get("allowed", True) else 'rejected',
        states=['published', 'rejected']))
def moderate(self, allowed=True):
    pass
```

### `custom` properties

Custom properties can be added by providing a dictionary to the
`custom` keyword on the `transition` decorator.

```
@transition(field=state,
            source='*',
            target='onhold',
            custom=dict(verbose='Hold for legal reasons'))
def legal_hold(self):
    """
    Side effects galore
    """
```

### `on_error` state

If the transition method raises an exception, you can provide a
specific target state

```
@transition(field=state, source='new', target='published', on_error='failed')
def publish(self):
   """
   Some exception could happen here
   """
```
### `state_choices`

Instead of passing a two-item iterable `choices` you can instead use the
three-element `state_choices`, the last element being a string reference
to a model proxy class.

The base class instance would be dynamically changed to the corresponding Proxy
class instance, depending on the state. Even for queryset results, you
will get Proxy class instances, even if the QuerySet is executed on the base class.

### Permissions

It is common to have permissions attached to each model transition.
`django-state-manager` handles this with `permission` keyword on the
`transition` decorator. `permission` accepts a permission string, or
callable that expects `instance` and `user` arguments and returns
True if the user can perform the transition.

.. code:: python
```
@transition(field=state, source='*', target='published',
            permission=lambda instance, user: not user.has_perm('myapp.can_make_mistakes'))
def publish(self):
    pass

@transition(field=state, source='*', target='removed',
            permission='myapp.can_remove_post')
def remove(self):
    pass
```
You can check permission with `has_transition_permission` method

.. code:: python
```
from django_state_manager.fsm import has_transition_perm
def publish_view(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    if not has_transition_perm(post.publish, request.user):
        raise PermissionDenied

    post.publish()
    post.save()
    return redirect('/')
```

### Model methods

`get_all_FIELD_transitions` Enumerates all declared transitions

`get_available_FIELD_transitions` Returns all transitions data
available in current state

`get_available_user_FIELD_transitions` Enumerates all transitions data
available in current state for provided user

### Foreign Key constraints support

If you store the states in the db table you could use FSMKeyField to
ensure Foreign Key database integrity.

In your model :

```
class DbState(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    label = models.CharField(max_length=255)

    def __unicode__(self):
        return self.label


class BlogPost(models.Model):
    state = FSMKeyField(DbState, default='new')

    @transition(field=state, source='new', target='published')
    def publish(self):
        pass
```
In your fixtures/initial\_data.json :

```
[
    {
        "pk": "new",
        "model": "myapp.dbstate",
        "fields": {
            "label": "_NEW_"
        }
    },
    {
        "pk": "published",
        "model": "myapp.dbstate",
        "fields": {
            "label": "_PUBLISHED_"
        }
    }
]
```

Note : source and target parameters in @transition decorator use pk
values of DBState model as names, even if field "real" name is used,
without \_id postfix, as field parameter.

### Integer Field support

You can also use `FSMIntegerField`. This is handy when you want to use
enum style constants.

```
class BlogPostStateEnum(object):
    NEW = 10
    PUBLISHED = 20
    HIDDEN = 30

class BlogPostWithIntegerField(models.Model):
    state = FSMIntegerField(default=BlogPostStateEnum.NEW)

    @transition(field=state, source=BlogPostStateEnum.NEW, target=BlogPostStateEnum.PUBLISHED)
    def publish(self):
        pass
```

### Signals

`django_state_manager.signals.pre_transition` and
`django_state_manager.signals.post_transition` are called before and after
allowed transition. No signals on invalid transition are called.

Arguments sent with these signals:

* **sender** The model class.

* **instance** The actual instance being processed

* **name** Transition name

* **source** Source model state

* **target** Target model state

### Optimistic locking

`django-state-manager` provides optimistic locking mixin, to avoid concurrent
model state changes. If model state was changed in database
`django_state_manager.fsm.ConcurrentTransition` exception would be raised on
model.save()

```python
    from django_state_manager.fsm import FSMField, ConcurrentTransitionMixin

    class BlogPost(ConcurrentTransitionMixin, models.Model):
        state = FSMField(default='new')
```

For guaranteed protection against race conditions caused by concurrently
executed transitions, make sure:

- Your transitions do not have any side effects except for changes in the database,
- You always run the save() method on the object within `django.db.transaction.atomic()` block.

Following these recommendations, you can rely on
ConcurrentTransitionMixin to cause a rollback of all the changes that
have been executed in an inconsistent (out of sync) state, thus
practically negating their effect.

## Conditions framework

The conditions framework is useful when dealing with authorization or a form of user validation in applications. 
You can define various conditions as function, and use instances of these classes to manage and combine those conditions 
flexibly.

Conditions are added to models to check for the availability of certain actions.


### Conditions
The Conditions class inherits from python's built-in list, and it is used to manage a list of functions (which are conditions that need to be checked). It has some key methods:
* `__add__`: This method allows to concatenate new conditions to our current list of conditions. It takes a list as 
* argument and returns a new Conditions object synthesizing the two lists.
* `__get__`: This magic method binds the conditions to an instance, making it possible for the conditions to be about 
  that particular instance.
* `__call__`: This method attempts to apply all the conditions to the instance. If a ConditionFailed exception occurs, 
  no error is raised at this level. It takes an instance and a user model as parameters.
* `as_bool`: This function is similar to __call__ but instead of calling the conditions, it returns a boolean value 
  based on whether the conditions pass or not. If a ConditionFailed exception has been raised it returns False, else it returns True.

### BoundConditions
The BoundConditions class is responsible for binding the conditions to a certain instance. It has two methods:
* `__init__`: This method initializes the BoundConditions object. It requires two parameters - conditions which is of 
type Conditions and an instance of any object.
* `__call__`: This method forwards a call to the __call__ method of the Conditions class with the instance and user as 
  arguments. It takes a user model as an argument.
* `as_bool`: This method simply checks if the conditions linked to the instance, when applied to the user, are 
  respected or not. It also takes a user model as an argument.