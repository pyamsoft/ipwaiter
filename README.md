# ipwaiter

## What Is This

`ipwaiter` works with `iptables` to manage groups of rules easily by putting  
specific rules groupings into their own chains, called `orders`

The syntax for an `order` is the same as `iptables` except that it does not  
include the `chain` name, nor does it include the command to `INPUT -I`,  
`APPEND -A`, or `DELETE -D`. The `order` file does not include this information  
because `ipwaiter` will automatically figure these out for you.

`ipwaiter` adds all of its order rules to three different chains, `input_orders`  
`forward_orders` and `output_orders`. `ipwaiter` does not automatically add these  
rule chains to the existing `iptables` setup. It is up to you, the end user, to  
add these chains into your `iptables` set up where you wish. The author for example  
mainly uses this script on a client machine which is configured to `DROP` all  
`INPUT` packets except for the ones allowed by these `order` groups.

## Working With Orders

Create orders using normal `iptables` syntax and place them into the `ipwaiter`  
system configuration directory at `/etc/ipwaiter` in the `orders` subdirectory.  
Order files are named as `%s.order` and are applied in the order they are listed.  

A single order can be placed by using `ipwaiter add <CHAIN> <order>` where `CHAIN`  
is either `INPUT` `FORWARD` or `OUTPUT`. The `order` is the name of the order file  
without the `.order` suffix, so a file named `test.order` would be applied  
to the `INPUT` chain using:
```
$ ipwaiter add INPUT test
```

Removing rules follows the same syntax, `ipwaiter remove <CHAIN> order` which  
will go and clear out the order chain and remove it from the iptables.

Applying an order again, once it has already been applied will generally be a  
no-op, though this is not guaranteed.

### System Setup

There are three general purpose commands which can be used with `ipwaiter`, which  
are `fire`, `hire`, and `rehire`.

`hire` parses the `system.conf` file in the  
system configuration directory `/etc/ipwaiter` and adds the specified `orders`  
into the provided `CHAINS` assuming the `orders` are valid.

`fire` removes all `order` related chains from the `iptables` instance to  
reset back to before the `ipwaiter` began working.

`rehire` first runs `fire` and then runs `hire`.

## Should I Use This?

No.

No guarantees, only support provided will be that it "works on my machine."
End user be warned.

## License

GPLv2

```
  The GPLv2 License

    Copyright (C) 2017  Peter Kenji Yamanaka

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
```
